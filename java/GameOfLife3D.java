import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;

public class GameOfLife3D {
  private static final Material LIVE = Material.SLIME_BLOCK;
  private static final Material DEAD = Material.AIR;

  private final World w;

  private final int xMin, yMin, zMin;
  private final int xMax, yMax, zMax;
  private final int xLen, yLen, zLen;

  private int maxAdjacentDims;
  private int birthMin, birthMax;
  private int starvationMax;
  private int suffocationMin;

  /** Buffer storing the next game state, reused for each step. */
  private final Material[][][] next;

  public GameOfLife3D(World w, int xMin, int xMax, int yMin, int yMax, int zMin, int zMax,
    int maxAdjacentDims, int birthMin, int birthMax, int starvationMax, int suffocationMin)
  {
    this.w = w;
    this.xMin = xMin; this.xMax = xMax; xLen = xMax - xMin + 1;
    this.yMin = yMin; this.yMax = yMax; yLen = yMax - yMin + 1;
    this.zMin = zMin; this.zMax = zMax; zLen = zMax - zMin + 1;
    setRules(maxAdjacentDims, birthMin, birthMax, starvationMax, suffocationMin);
    next = new Material[xLen][yLen][zLen];
  }

  public void setRules(int maxAdjacentDims, int birthMin, int birthMax, int starvationMax, int suffocationMin) {
    this.maxAdjacentDims = maxAdjacentDims;
    this.birthMin = birthMin;
    this.birthMax = birthMax;
    this.starvationMax = starvationMax;
    this.suffocationMin = suffocationMin;
  }

  public static boolean live(Material m) { return m == LIVE; }
  public static boolean dead(Material m) { return m == Material.AIR || m == Material.CAVE_AIR; }
  public static boolean live(Block b) { return live(b.getType()); }
  public static boolean dead(Block b) { return dead(b.getType()); }

  public Block block(int x, int y, int z) { return w.getBlockAt(x + xMin, y + yMin, z + zMin); }
  public boolean live(int x, int y, int z) { return live(block(x, y, z)); }
  public boolean dead(int x, int y, int z) { return dead(block(x, y, z)); }

  public void step() {
    // compute next state
    for (int z=0; z<zLen; z++) {
      for (int y=0; y<yLen; y++) {
        for (int x=0; x<xLen; x++) {
          final Block b = block(x, y, z);
          final Material m = b.getType();
          next[x][y][z] = m;

          final boolean live = live(m);
          final boolean dead = dead(m);
          if (!live && !dead) continue; // this block is not part of the game

          int liveCount = 0;
          if (live(x-1, y, z)) liveCount++; // n
          if (live(x+1, y, z)) liveCount++; // e
          if (live(x, y-1, z)) liveCount++; // d
          if (live(x, y+1, z)) liveCount++; // u
          if (live(x, y, z-1)) liveCount++; // n
          if (live(x, y, z+1)) liveCount++; // s
          if (live(x-1, y-1, z)) liveCount++; // wd
          if (live(x-1, y+1, z)) liveCount++; // wu
          if (live(x+1, y-1, z)) liveCount++; // ed
          if (live(x+1, y+1, z)) liveCount++; // eu
          if (live(x-1, y, z-1)) liveCount++; // wn
          if (live(x-1, y, z+1)) liveCount++; // ws
          if (live(x+1, y, z-1)) liveCount++; // en
          if (live(x+1, y, z+1)) liveCount++; // es
          if (live(x, y-1, z-1)) liveCount++; // dn
          if (live(x, y-1, z+1)) liveCount++; // ds
          if (live(x, y+1, z-1)) liveCount++; // un
          if (live(x, y+1, z+1)) liveCount++; // us
          if (live(x-1, y-1, z-1)) liveCount++; // wdn
          if (live(x-1, y-1, z+1)) liveCount++; // wds
          if (live(x-1, y+1, z-1)) liveCount++; // wun
          if (live(x-1, y+1, z+1)) liveCount++; // wus
          if (live(x+1, y-1, z-1)) liveCount++; // edn
          if (live(x+1, y-1, z+1)) liveCount++; // eds
          if (live(x+1, y+1, z-1)) liveCount++; // eun
          if (live(x+1, y+1, z+1)) liveCount++; // eus

          if (live) {
            // should the cell die?
            if (liveCount <= starvationMax || liveCount >= suffocationMin) next[x][y][z] = DEAD;
          }
          else {
            // should the cell be born?
            if (liveCount >= birthMin && liveCount <= birthMax) next[x][y][z] = LIVE;
          }
        }
      }
    }

    // assign next state
    for (int z=0; z<zLen; z++) {
      for (int y=0; y<yLen; y++) {
        for (int x=0; x<xLen; x++) {
          final Block b = block(x, y, z);
          final Material now = b.getType();
          final Material soon = next[x][y][z];
          if (now != soon) b.setType(soon);
        }
      }
    }
  }

  public void shuffle(final double saturation) {
    for (int z=0; z<zLen; z++) {
      for (int y=0; y<yLen; y++) {
        for (int x=0; x<xLen; x++) {
          final Block b = block(x, y, z);
          final Material m = b.getType();

          final boolean live = live(m);
          final boolean dead = dead(m);
          if (!live && !dead) continue; // this block is not part of the game

          final Material rm = Math.random() < saturation ? LIVE : DEAD;
          if (m != rm) b.setType(rm);
        }
      }
    }
  }
}
