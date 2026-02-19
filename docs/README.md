# LaTeX Documentation 

## VS Code Setup for LaTeX

To work with LaTeX in VS Code, install the **LaTeX Workshop** extension. 
You’ll also need LaTeX dependencies. On Ubuntu, install them with:

``` bash
sudo apt install texlive-full latexmk biber
```

### Configure LaTeX Workshop to Use a Build Directory

By default, LaTeX Workshop generates output files (e.g., `.aux`, `.log`, `.pdf`) alongside your source files.
To keep your project tidy, configure it to place outputs inside a `build/` directory.

In the docs directory, create (or edit) `.vscode/settings.json`:
``` json
{
  // Put all LaTeX outputs into docs/build instead of next to main.tex
  "latex-workshop.latex.outDir": "../build",

  "latex-workshop.latex.tools": [
    {
      "name": "latexmk",
      "command": "latexmk",
      "args": [
        "-synctex=1",
        "-interaction=nonstopmode",
        "-file-line-error",
        "-pdf",
        "-outdir=%OUTDIR%",
        "-auxdir=%OUTDIR%/aux",
        "%DOC%"
      ]
    },
    {
      "name": "makeglossaries",
      "command": "makeglossaries",
      "args": [
        "-d", "%OUTDIR%/aux",
        "%DOCFILE%"
      ]
    }
  ],

  "latex-workshop.latex.recipes": [
    {
      "name": "latexmk → makeglossaries → latexmk",
      "tools": [
        "latexmk",
        "makeglossaries",
        "latexmk"
      ]
    }
  ],

  "latex-workshop.latex.recipe.default": "lastUsed"
}

```
Optionally: create `build\aux` directory to keep aux data separeted from final pdf. `build\aux` is ignored so no further cleaning is required. 

After saving, LaTeX Workshop will compile your project using latexmk, placing all generated files in `build/`.


## Clean Up on Demand
If you occasionally want to clear build artifacts:

### From the terminal (inside your project directory)

``` bash
latexmk -c   # Remove auxiliary files, keep PDF
latexmk -C   # Remove auxiliary files and PDF
```

### From VS Code

Open the Command Palette and run:
> LaTeX Workshop: Clean up auxiliary files