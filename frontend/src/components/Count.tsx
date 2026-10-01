import { animate, useMotionValue, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import { EASE } from "../lib/format";

/** A number that glides from its previous value to the new one. */
export default function Count({ value, digits = 0, suffix = "" }: { value: number; digits?: number; suffix?: string }) {
  const mv = useMotionValue(value);
  const [shown, setShown] = useState(value);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) {
      mv.set(value);
      setShown(value);
      return;
    }
    const controls = animate(mv, value, { duration: 0.7, ease: EASE, onUpdate: setShown });
    return () => controls.stop();
  }, [value, mv, reduce]);

  return (
    <>
      {shown.toFixed(digits)}
      {suffix}
    </>
  );
}
