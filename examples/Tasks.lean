-- Trusted task source. A placeholder is allowed ONLY here, never in a candidate.
-- The model receives preceding context and the target header, not this body.
namespace CompanionExample

def twice (n : Nat) : Nat := n + n

theorem twice_zero : twice 0 = 0 := by
  rfl

theorem add_zero (n : Nat) : n + 0 = n := by
  rfl

end CompanionExample
