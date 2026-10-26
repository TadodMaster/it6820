import com.cburch.logisim.file.*;
import com.cburch.logisim.circuit.*;
import com.cburch.logisim.comp.*;
import java.io.File;

public class Ends {
  public static void main(String[] a) throws Exception {
    System.setProperty("java.awt.headless", "true");
    Loader l = new Loader(null);
    LogisimFile f = LogisimFile.load(new File(a[0]), l);
    for (Circuit c : f.getCircuits()) {
      if (a.length > 1 && !c.getName().equals(a[1])) continue;
      System.out.println("== " + c.getName());
      for (Component k : c.getNonWires()) {
        StringBuilder sb = new StringBuilder();
        sb.append(k.getFactory().getName()).append(" @").append(k.getLocation())
          .append(" bounds=").append(k.getBounds()).append(" ends=");
        int i = 0;
        for (EndData e : k.getEnds()) {
          sb.append(" [").append(i++).append(":").append(e.getLocation().getX()).append(",")
            .append(e.getLocation().getY()).append(" w").append(e.getWidth().getWidth())
            .append(e.isInput() ? "I" : "").append(e.isOutput() ? "O" : "").append("]");
        }
        System.out.println(sb);
      }
    }
    System.exit(0);
  }
}
