-- Minimal specification example, not the complete MG-01 engine.
namespace Scorecard
structure State where
  used : Fin 13 → Bool

def record (s : State) (category : Fin 13) : Option State :=
  if s.used category then none
  else some { used := fun c => if c == category then true else s.used c }

-- A category already marked used cannot be recorded again.
theorem no_double_write (s : State) (category : Fin 13)
    (h : s.used category = true) : record s category = none := by
  simp [record, h]
end Scorecard
