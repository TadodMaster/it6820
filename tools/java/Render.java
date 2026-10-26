import com.cburch.logisim.file.*;
import com.cburch.logisim.circuit.*;
import com.cburch.logisim.comp.*;
import com.cburch.logisim.data.Bounds;
import com.cburch.logisim.proj.Project;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
import javax.swing.JPanel;

public class Render {
  public static void main(String[] a) throws Exception {
    System.setProperty("java.awt.headless", "true");
    Loader l = new Loader(null);
    LogisimFile f = LogisimFile.load(new File(a[0]), l);
    Project proj = new Project(f);
    File outDir = new File(a[1]);
    outDir.mkdirs();
    double scale = a.length > 3 ? Double.parseDouble(a[3]) : 1.0;
    for (Circuit c : f.getCircuits()) {
      if (a.length > 2 && !a[2].equals("ALL") && !c.getName().equals(a[2])) continue;
      proj.setCurrentCircuit(c);
      CircuitState cs = proj.getCircuitState(c);
      Bounds b = c.getBounds();
      int pad = 40;
      int w = (int) ((b.getWidth() + 2 * pad) * scale), h = (int) ((b.getHeight() + 2 * pad) * scale);
      BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
      Graphics2D g = img.createGraphics();
      g.setColor(Color.WHITE);
      g.fillRect(0, 0, w, h);
      g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
      g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
      g.scale(scale, scale);
      g.translate(pad - b.getX(), pad - b.getY());
      Graphics2D g2 = (Graphics2D) g.create();
      ComponentDrawContext ctx = new ComponentDrawContext(new JPanel(), c, cs, g, g2);
      ctx.setShowState(false);
      ctx.setShowColor(true);
      c.draw(ctx, null);
      g.dispose();
      File out = new File(outDir, c.getName() + ".png");
      ImageIO.write(img, "png", out);
      System.out.println("wrote " + out + " " + w + "x" + h);
    }
    System.exit(0);
  }
}
