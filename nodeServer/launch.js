// Launch server Node.js
var module_server = require("./mods/server");
server = module_server.start();
server81 = module_server.start81();

// Launch Python main
var pythonShell = require('python-shell');

pythonShell.run('./scripts/main.py', err => {
  if (err) throw err;
  console.log('Python script has ended');
});
