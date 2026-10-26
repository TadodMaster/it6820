import com.cburch.logisim.circuit.*;
import com.cburch.logisim.comp.Component;
import com.cburch.logisim.data.Value;
import com.cburch.logisim.file.*;
import com.cburch.logisim.instance.StdAttr;
import com.cburch.logisim.proj.Project;
import com.cburch.logisim.std.memory.*;

import java.io.File;
import java.nio.file.Files;
import java.util.*;

/**
 * Headless program runner for the RV32I Logisim project.
 *
 * usage: Run <file.circ> <circuit> <program.hex> <cycles> [trace]
 *
 * Loads the program into the circuit's ROM, runs the clock for <cycles> full cycles and prints
 *   CYCLES=n, PC=hhhhhhhh, x0..x31=hhhhhhhh, MEM[addr]=hhhhhhhh (non-zero words of the data RAM).
 * With "trace" it also prints "T <cycle> PC=hhhhhhhh" after every cycle.
 * Registers of the register file are found by their label (x0..x31); the PC register by the label PC.
 */
public class Run {
  /** RegisterData / MemState are package-private in Logisim, so use reflection. */
  static Object call(Object o, String method) throws Exception {
    java.lang.reflect.Method m = o.getClass().getMethod(method);
    m.setAccessible(true);
    return m.invoke(o);
  }

  static long val(Object data) throws Exception {
    if (data == null) return 0L;
    Value v = (Value) call(data, "getValue");
    return v.isFullyDefined() ? v.toLongValue() : -1L;
  }

  static String label(Component c) {
    if (!c.getAttributeSet().containsAttribute(StdAttr.LABEL)) return "";
    String l = c.getAttributeSet().getValue(StdAttr.LABEL);
    return l == null ? "" : l;
  }

  /** value of the net at a point: "@x,y" in the top circuit or "@SubCircuit:x,y" inside a sub-circuit */
  static String probe(CircuitState cs, String arg) {
    String spec = arg.substring(1);
    CircuitState st = cs;
    if (spec.contains(":")) {
      st = findSub(cs, spec.substring(0, spec.indexOf(':')));
      spec = spec.substring(spec.indexOf(':') + 1);
    }
    if (st == null) return "no such circuit";
    String[] xy = spec.split(",");
    return st.getValue(com.cburch.logisim.data.Location.create(Integer.parseInt(xy[0]), Integer.parseInt(xy[1]), false)).toHexString();
  }

  static CircuitState findSub(CircuitState root, String circuitName) {
    for (CircuitState s : root.getSubstates()) {
      if (s.getCircuit().getName().equals(circuitName)) return s;
      CircuitState r = findSub(s, circuitName);
      if (r != null) return r;
    }
    return null;
  }

  public static void main(String[] a) throws Exception {
    System.setProperty("java.awt.headless", "true");
    File file = new File(a[0]);
    String circuitName = a[1];
    int cycles = Integer.parseInt(a[3]);
    boolean trace = a.length > 4 && a[4].equals("trace");

    Loader loader = new Loader(null);
    LogisimFile lf = LogisimFile.load(file, loader);
    Circuit top = lf.getCircuit(circuitName);
    if (top == null) throw new IllegalArgumentException("no circuit " + circuitName);

    // program -> ROM
    List<Long> words = new ArrayList<>();
    for (String line : Files.readAllLines(new File(a[2]).toPath())) {
      line = line.trim();
      if (line.isEmpty() || line.startsWith("v2.0")) continue;
      for (String t : line.split("\\s+")) words.add(Long.parseLong(t, 16));
    }
    int romCount = 0;
    for (Component c : top.getNonWires()) {
      if (c.getFactory().getName().equals("ROM")) {
        MemContents mc = c.getAttributeSet().getValue(Rom.CONTENTS_ATTR);
        mc.clear();
        for (int i = 0; i < words.size(); i++) mc.set(i, words.get(i));
        romCount++;
      }
    }
    if (romCount != 1) throw new IllegalStateException("expected 1 ROM in " + circuitName + ", found " + romCount);

    Project proj = new Project(lf);
    CircuitState cs = CircuitState.createRootState(proj, top, Thread.currentThread());
    Propagator prop = cs.getPropagator();
    prop.propagate();

    Component pc = null;
    for (Component c : top.getNonWires())
      if (c.getFactory().getName().equals("Register") && label(c).equals("PC")) pc = c;
    if (pc == null) throw new IllegalStateException("no register labelled PC in " + circuitName);

    for (int i = 1; i <= cycles; i++) {
      for (int half = 0; half < 2; half++) {
        prop.toggleClocks();
        prop.propagate();
      }
      if (trace) {
        StringBuilder sb = new StringBuilder("T " + i + " PC=" + ((Value) call(cs.getData(pc), "getValue")).toHexString());
        for (int k = 5; k < a.length; k++)
          if (a[k].startsWith("@")) sb.append(" ").append(probe(cs, a[k]));
        System.out.println(sb);
      }
    }

    // optional debug probes: arguments "@x,y" (or "@Circuit:x,y") after the 5th argument print the value of the net at that point
    for (int k = 5; k < a.length; k++)
      if (a[k].startsWith("@")) System.out.println("PROBE " + a[k] + " = " + probe(cs, a[k]));
    System.out.println("CYCLES=" + cycles);
    System.out.printf("PC=%08x%n", val(cs.getData(pc)) & 0xFFFFFFFFL);

    CircuitState rf = findSub(cs, "RegisterFile");
    long[] regs = new long[32];
    Arrays.fill(regs, -1);
    if (rf != null) {
      for (Component c : rf.getCircuit().getNonWires()) {
        String l = label(c);
        if (c.getFactory().getName().equals("Register") && l.matches("x\\d+"))
          regs[Integer.parseInt(l.substring(1))] = val(rf.getData(c));
      }
    }
    for (int i = 0; i < 32; i++) System.out.printf("x%d=%08x%n", i, regs[i] & 0xFFFFFFFFL);

    CircuitState mem = findSub(cs, "Memory");
    if (mem != null) {
      for (Component c : mem.getCircuit().getNonWires()) {
        if (c.getFactory().getName().equals("RAM")) {
          MemContents mc = (MemContents) call(mem.getData(c), "getContents");
          for (long ad = 0; ad < 256; ad++) {
            long v = mc.get(ad);
            if (v != 0) System.out.printf("MEM[%03x]=%08x%n", ad * 4, v & 0xFFFFFFFFL);
          }
        }
      }
    }
    System.exit(0);
  }
}
