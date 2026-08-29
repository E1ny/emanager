#target photoshop
var inputFile = new File('C:/Users/32730/Documents/Codex/2026-08-30/skill-plugin-x20/work/target.jpg');
var outputFile = new File('C:/Users/32730/Documents/Codex/2026-08-30/skill-plugin-x20/work/styled-photoshop.jpg');
var doc = app.open(inputFile);
var layer = doc.activeLayer;
layer.adjustBrightnessContrast(0, -32.400);
layer.adjustColorBalance([25.000, 0, -25.000], [0, 0, 0], [12.500, 0, -12.500], true);
var options = new JPEGSaveOptions();
options.quality = 12;
doc.saveAs(outputFile, options, true);
doc.close(SaveOptions.DONOTSAVECHANGES);
