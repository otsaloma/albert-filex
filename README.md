Albert Extension Filex
======================

Filex is a Python extension for the [Albert][] launcher to index, find
and open files and folders.

[Albert]: https://albertlauncher.github.io/

You need the Python bindings for Gio (part of GLib) to use Filex. On
Debian/Ubuntu run the following command to install the dependencies.

```bash
sudo apt install gir1.2-glib-2.0 python3-gi
```

To install, run

```bash
sudo make PREFIX=/usr/local install
```

Activate Filex in Albert's preferences under Extensions / Python /
Filex. Configure paths to index by editing `~/.config/albert/filex.json`.
Paths are interpreted as glob patterns using Python's [glob][] module.

[glob]: https://docs.python.org/3/library/glob.html
