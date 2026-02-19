'use strict';

const { execSync, execFileSync, spawn: spawnProcess } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

const isWin = process.platform === 'win32';
const OTTER_HOME = path.join(os.homedir(), '.otter');
const VENV_DIR = path.join(OTTER_HOME, 'venv');
const OTTER_BIN = isWin
  ? path.join(VENV_DIR, 'Scripts', 'otter.exe')
  : path.join(VENV_DIR, 'bin', 'otter');

function write(msg) {
  process.stdout.write(msg);
}

function run(cmd, opts = {}) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: 'pipe', ...opts }).trim();
  } catch {
    return null;
  }
}

function runFile(file, args, opts = {}) {
  try {
    return execFileSync(file, args, { encoding: 'utf8', stdio: 'pipe', ...opts }).trim();
  } catch {
    return null;
  }
}

function commandExists(cmd) {
  if (isWin) {
    return run(`where ${cmd}`) !== null;
  }
  return run(`command -v ${cmd}`) !== null;
}

function parsePythonVersion(versionStr) {
  const match = versionStr && versionStr.match(/Python (\d+)\.(\d+)\.(\d+)/);
  if (!match) return null;
  return { major: parseInt(match[1]), minor: parseInt(match[2]), patch: parseInt(match[3]) };
}

function findPython() {
  for (const cmd of ['python3', 'python']) {
    const out = run(`${cmd} --version`);
    const ver = parsePythonVersion(out);
    if (ver && ver.major === 3 && ver.minor >= 10) {
      return { cmd, version: `${ver.major}.${ver.minor}.${ver.patch}` };
    }
  }
  return null;
}

function findUv() {
  // Check common uv locations
  const uvPaths = [
    'uv',
    path.join(os.homedir(), '.local', 'bin', 'uv'),
    path.join(os.homedir(), '.cargo', 'bin', 'uv'),
  ];
  if (isWin) {
    uvPaths.push(path.join(os.homedir(), '.local', 'bin', 'uv.exe'));
    uvPaths.push(path.join(os.homedir(), 'AppData', 'Local', 'uv', 'uv.exe'));
  }

  for (const uvPath of uvPaths) {
    const out = runFile(uvPath, ['--version']);
    if (out) return uvPath;
  }
  return null;
}

async function installUv() {
  return new Promise((resolve, reject) => {
    let cmd, args;
    if (isWin) {
      cmd = 'powershell';
      args = ['-c', 'irm https://astral.sh/uv/install.sh | iex'];
    } else {
      cmd = 'sh';
      args = ['-c', 'curl -LsSf https://astral.sh/uv/install.sh | sh'];
    }

    const child = spawnProcess(cmd, args, { stdio: 'pipe', env: { ...process.env, UV_INSTALL_DIR: path.join(os.homedir(), '.local', 'bin') } });
    let stderr = '';
    child.stderr.on('data', (d) => { stderr += d.toString(); });
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`uv install failed (exit ${code}): ${stderr}`));
    });
    child.on('error', reject);
  });
}

async function installOtter(uvPath) {
  // Create venv
  if (!fs.existsSync(VENV_DIR)) {
    fs.mkdirSync(OTTER_HOME, { recursive: true });
    const result = run(`"${uvPath}" venv "${VENV_DIR}"`);
    if (result === null) {
      // Try without quotes for systems that don't need them
      const r2 = runFile(uvPath, ['venv', VENV_DIR]);
      if (r2 === null) throw new Error('Failed to create virtual environment');
    }
  }

  // Install otter-ml from GitHub
  return new Promise((resolve, reject) => {
    const child = spawnProcess(uvPath, [
      'pip', 'install',
      '--python', VENV_DIR,
      'git+https://github.com/otter-ml/otter.git'
    ], { stdio: 'pipe' });

    let stderr = '';
    child.stderr.on('data', (d) => { stderr += d.toString(); });
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`otter-ml install failed (exit ${code}): ${stderr}`));
    });
    child.on('error', reject);
  });
}

async function checkAndInstall() {
  // Fast path: otter already installed in our venv
  if (fs.existsSync(OTTER_BIN)) {
    const out = runFile(OTTER_BIN, ['--version']);
    if (out !== null) return OTTER_BIN;
  }

  // Fast path: otter available on PATH
  if (commandExists('otter')) {
    const otterPath = run(isWin ? 'where otter' : 'command -v otter');
    if (otterPath) {
      const out = run(`"${otterPath}" --version`);
      if (out !== null) return otterPath;
    }
  }

  // Need to install
  write('\n🦦 Setting up Otter for the first time...\n');

  // Check Python
  write('   Checking Python... ');
  const python = findPython();
  if (!python) {
    write('✗\n\n');
    console.error('   Python 3.10+ is required but not found.');
    console.error('   Install from https://python.org or via your package manager.\n');
    process.exit(1);
  }
  write(`✓ Python ${python.version} found\n`);

  // Check/install uv
  write('   Checking uv... ');
  let uvPath = findUv();
  if (!uvPath) {
    write('not found\n');
    write('   Installing uv (fast Python installer)... ');
    try {
      await installUv();
      uvPath = findUv();
      if (!uvPath) throw new Error('uv not found after install');
      write('✓\n');
    } catch (err) {
      write('✗\n\n');
      console.error(`   Failed to install uv: ${err.message}`);
      console.error('   Install manually: curl -LsSf https://astral.sh/uv/install.sh | sh\n');
      process.exit(1);
    }
  } else {
    write('✓\n');
  }

  // Install otter-ml
  write('   Installing otter-ml... ');
  try {
    await installOtter(uvPath);
    write('✓\n');
  } catch (err) {
    write('✗\n\n');
    console.error(`   Failed to install otter-ml: ${err.message}\n`);
    process.exit(1);
  }

  if (!fs.existsSync(OTTER_BIN)) {
    console.error('\n   otter binary not found after install. Please report this issue.');
    console.error(`   Expected: ${OTTER_BIN}\n`);
    process.exit(1);
  }

  write('   Ready! Starting Otter...\n\n');
  return OTTER_BIN;
}

module.exports = { checkAndInstall };
