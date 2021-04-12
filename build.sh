#!/bin/sh

# Compiles Java-side code, wrapping compiled classes into a JAR file, We delete
# the classes afteward because otherwise, subsequently, once any class files
# reside here, Jython erroneously treats this Python module as a Java package
# forevermore until the Minecraft server is restarted.

dir=$(cd "$(dirname "$0")" && pwd)
mcroot=$(cd "$dir/../.." && pwd)
indir="$dir/java"
builddir="$dir/build"
mkdir -p "$builddir" &&
javac -cp "$mcroot/spigot.jar" -d "$builddir" "$indir"/*.java &&
(cd "$builddir" && jar cf "$dir/mcx.jar" .) &&
rm -rf "$builddir"
