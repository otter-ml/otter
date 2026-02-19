#!/usr/bin/env node

const { checkAndInstall } = require('../src/install');
const { spawn } = require('child_process');

async function main() {
  const otterPath = await checkAndInstall();

  const args = process.argv.slice(2);

  const child = spawn(otterPath, args, {
    stdio: 'inherit',
    shell: false
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });

  child.on('error', (err) => {
    console.error('Failed to start otter:', err.message);
    process.exit(1);
  });
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});
