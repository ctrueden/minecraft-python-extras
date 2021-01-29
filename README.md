Extra functions for
[minecraft-python](https://github.com/Macuyiko/minecraft-python/releases).


## INSTALLATION

1. Install [Spigot](https://www.spigotmc.org/).

2. Download
   [minecraft-python](https://github.com/Macuyiko/minecraft-python/releases).
   Drop into `plugins/` folder of the spigot server.

3. In your Spigot installation:
   ```
   mkdir python
   cd python
   git clone git://github.com/ctrueden/minecraft-python-extras extras
   ```


## EXECUTION

1. Launch server.

2. Launch a Minecraft client at version 1.15.2 (use Java launcher), and connect
   to external server at whatever IP the server is on, on port 25565 (or as
   customized in `server.properties`).

3. Visit http://<your-server>:8080/ to access the Jython console via a web browser.
   * It also works to `telnet <your-server> 44444`.
   * Or use `remote-client.py` from minecraft-python working copy.
   * Inside Minecraft, you can `/py <code-to-execute>` to run one-liners.

4. In the Jython interpreter, try:
   ```
   from extras import *
   me = pov('myplayername')
   help(me)
   ```
