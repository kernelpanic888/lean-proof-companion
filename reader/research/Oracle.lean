-- PC-01: a small scorecard specification, independent of the full MG-01 engine.
-- Lean 4.31.0-rc1, no Mathlib dependency.
namespace Scorecard
structure State where
  used : Fin 13 → Bool

def record (s : State) (category : Fin 13) : Option State :=
  if s.used category then none
  else some { used := fun c => if c == category then true else s.used c }

theorem no_double_write (s : State) (category : Fin 13)
    (h : s.used category = true) : record s category = none := by
  simp [record, h]

theorem unused_is_recordable (s : State) (category : Fin 13)
    (h : s.used category = false) : (record s category).isSome = true := by
  simp [record, h]

theorem record_marks_used (s : State) (category : Fin 13) (t : State)
    (h : record s category = some t) : t.used category = true := by
  simp only [record] at h
  split at h
  · contradiction
  · cases h
    simp

theorem record_preserves_other (s : State) (category other : Fin 13)
    (t : State) (h : record s category = some t) (hne : other ≠ category) :
    t.used other = s.used other := by
  simp only [record] at h
  split at h
  · contradiction
  · cases h
    simp [hne]
end Scorecard

def decodeMask (mask : Nat) : Scorecard.State :=
  { used := fun c => (mask / 2^c.val) % 2 == 1 }

def encodeMask (s : Scorecard.State) : Nat :=
  (List.finRange 13).foldl (fun acc c => if s.used c then acc + 2^c.val else acc) 0

def main : IO Unit := do
  let stdout ← IO.getStdout
  for mask in [:8192] do
    let row := (List.finRange 13).map fun c =>
      match Scorecard.record (decodeMask mask) c with
      | none => "null"
      | some state => toString (encodeMask state)
    stdout.putStrLn ("[" ++ String.intercalate "," row ++ "]")
