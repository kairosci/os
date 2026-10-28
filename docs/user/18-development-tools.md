# Development Tools

## Alternative Editors

Arch ships with [Neovim](https://neovim.io/) by default, but if you'd like something a bit more mainstream and familiar, you can run the Arch Menu (`Super + Space`) and see the options under _Install > Editor_. We have VSCode, Cursor, Zed, Sublime Text, Helix, Vim, and Emacs listed there. If you don't find what you're looking for, checkout _Install > Package_, and see if it isn't in an Arch package (and if not, try _Install > AUR_ to check the AUR).

The original `vi` editor is also available out of the box. Run `vi filename` to edit a file in the terminal.

Theme matching is offered for `VSCode`, `Cursor`, `VSCodium`, and `Helix`.

You can set the system-wide default editor under `Setup > Defaults > Editor`.

## Environment

Arch supports setting up a whole host of development environments through the _Install > Development_ section of the Arch Menu (`Super + Space`). You'll of course find _Ruby on Rails_, but also all three major runtimes for JavaScript (Node.js, Bun, Deno), as well as popular PHP frameworks like Laravel and Symfony. Oh, and there's Go, Rust, Python, Java, Elixir (with Phoenix), .NET, OCaml, Zig, Clojure, and Scala too. It's a very broad selection!

The majority of these environments are managed by [Mise](https://mise.jdx.dev/). It's a tool that lets you install and run multiple versions of a programming language on the same machine. It's like rbenv or rvm for Ruby or virtualenv for Python, but it works for a bunch of different environments.

To install, say, Ruby, you'd run `mise use -g ruby`, which will both install Ruby and set it as the global default. Or, if your project has a .ruby-version file, you can just run `mise i` in the root of that project.

## Preinstalled CLI tools

Arch makes tools such as `gh` and `uv` available through [mise's lazy installation](https://mise.jdx.dev/dev-tools/shims.html#lazy-tools). The first time you run one, mise installs it. Later runs reuse the installed version; they do not check for an update on every launch.

You can inspect the defaults or install them ahead of time:

```bash
mise ls --current              # List the tools configured for this directory
mise install gh               # Install one tool now
mise install --include-lazy    # Install all configured tools, including lazy tools
```

Run `archctl update` to update installed tools with the rest of Arch. The `mup` alias updates mise-managed tools only. To add another tool to your own configuration, use `mise use -g <tool>`.

Python setup also installs `uv` through mise. Removing the Python development environment leaves `uv` available as an independent tool.

## Docker

[Docker](https://www.docker.com/) hardly needs any introduction. It allows you to run isolated containers, and Arch installs everything needed to run it well, including Docker itself and [Docker Compose](https://docs.docker.com/compose/).

By default your user is *not* in the `docker` group. That group is effectively root access: a container can bind-mount `/` and take over the machine. Use Docker with `sudo` (`sudo docker ps`, `sudo docker compose up`); graphical tools that need the daemon ask for authorization. If your account is already in the `docker` group, remove it with `sudo gpasswd -d "$USER" docker` and start a new session for the change to take effect.

You can setup the common databases for local development in Docker using _Install > Development > Docker DB_ in the Arch menu.

## GitHub CLI

[GitHub CLI](https://cli.github.com/) is available as `gh` for working with repositories, issues, and pull requests from the terminal. Run `gh auth login` to install it on first use and authenticate, then `gh repo clone org/repo` to clone a repository. Run `gh --help` to explore its commands.

For a terminal interface to pull requests, run `ghui`; mise installs it on first use too. [Lazygit](https://github.com/jesseduffield/lazygit) is preinstalled for working with Git itself.
