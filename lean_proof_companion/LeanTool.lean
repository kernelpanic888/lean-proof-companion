import Lean
open Lean Lean.Elab

private def js (xs : List (String × Json)) : Json := Json.mkObj xs
private def str (s : String) : Json := toJson s
private def nm (s : String) : Name := s.toName

private partial def tree (s : Syntax) : Json := js [
  ("kind", str s.getKind.toString),
  ("start", toJson (s.getPos?.map (·.byteIdx))),
  ("end", toJson (s.getTailPos?.map (·.byteIdx))),
  ("text", str (s.getId.toString)),
  ("children", toJson (s.getArgs.map tree))]

private def loadSource (source : String) : IO Frontend.State := do
  let ictx := Parser.mkInputContext source "Task.lean"
  let (header, ps, messages) ← Parser.parseHeader ictx
  let opts := ({} : Options).setBool `Elab.async false
  let (env, messages) ← processHeader header opts messages ictx (mainModule := `Candidate)
  IO.processCommands ictx ps (Command.mkState env messages opts)

private def diagnostics (messages : MessageLog) : IO (Array Json) := do
  messages.toArray.mapM fun m => do
    return js [("severity", str (toString m.severity)), ("message", str (← m.data.toString))]

private def save (path : String) (value : Json) : IO Unit := IO.FS.writeFile path value.compress

unsafe def main (args : List String) : IO UInt32 := do
  enableInitializersExecution
  initSearchPath (← findSysroot)
  try
    match args with
    | ["parse", path, result] =>
      let source ← IO.FS.readFile path
      let ictx := Parser.mkInputContext source path
      let (header, ps, messages) ← Parser.parseHeader ictx
      let opts := ({} : Options).setBool `Elab.async false
      let (env, messages) ← processHeader header opts messages ictx (mainModule := `Candidate)
      let mut state : Frontend.State := {commandState := Command.mkState env messages opts, parserState := ps, cmdPos := ps.pos}
      let mut commands : Array Json := #[]
      repeat
        let ns := state.commandState.scopes.head!.currNamespace.toString
        let (done, next) ← Frontend.processCommand.run {inputCtx := ictx} |>.run state
        state := next
        commands := commands.push (js [("namespace", str ns), ("scope_depth", toJson (state.commandState.scopes.length - 1)), ("scopes", toJson (state.commandState.scopes.dropLast.map (·.header))), ("syntax", tree state.commands.back!)])
        if done then break
      save result (js [("commands", toJson commands),
        ("diagnostics", toJson (← diagnostics state.commandState.messages)),
        ("errors", toJson state.commandState.messages.hasErrors)])
      return (0 : UInt32)
    | ["term", path, result] =>
      let env ← importModules #[{module := `Lean}] {} 0 (loadExts := true)
      let answer := Parser.runParserCategory env `term (← IO.FS.readFile path)
      match answer with
      | .error message => save result (js [("ok", toJson false), ("error", str message)])
      | .ok parsed => save result (js [("ok", toJson true), ("syntax", tree parsed)])
      return (0 : UInt32)
    | ["compile", path, artifact, result] =>
      let state ← loadSource (← IO.FS.readFile path)
      let errors := state.commandState.messages.hasErrors
      if !errors then writeModule state.commandState.env artifact
      save result (js [("errors", toJson errors), ("diagnostics", toJson (← diagnostics state.commandState.messages))])
      return if errors then (1 : UInt32) else 0
    | ["inspect", moduleName, declaration, expectedFile, result] =>
      let expected ← loadSource (← IO.FS.readFile expectedFile)
      enableInitializersExecution
      let env ← importModules #[{module := nm moduleName}] {} 0 (loadExts := true)
      let name := nm declaration
      let some actual := env.find? name | throw (IO.userError "candidate declaration missing")
      let some target := expected.commandState.env.find? name | throw (IO.userError s!"expected declaration missing: {← diagnostics expected.commandState.messages}")
      let ctx : Core.Context := {fileName := "audit", fileMap := FileMap.ofString ""}
      let (same, _, _) ← Meta.MetaM.toIO (Meta.isDefEq actual.type target.type) ctx {env := env}
      let axs ← Core.CoreM.toIO' (collectAxioms name) ctx {env := env}
      save result (js [("same_type", toJson same), ("is_theorem", toJson actual.isTheorem),
        ("axioms", toJson (axs.map (·.toString))), ("type", str (toString actual.type))])
      return (0 : UInt32)
    | _ => throw (IO.userError "invalid arguments")
  catch error =>
    IO.eprintln error.toString
    return (2 : UInt32)
