import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {loadDatabaseEnv} from './prisma-env.mjs';

loadDatabaseEnv();
const command=process.argv[2];
if(!['generate','validate','format'].includes(command))throw new Error('Lệnh không được hỗ trợ bởi helper này.');
const result=spawnSync(process.execPath,[fileURLToPath(new URL('../node_modules/prisma/build/index.js',import.meta.url)),command,'--schema',fileURLToPath(new URL('../prisma/schema.prisma',import.meta.url))],{stdio:'inherit',env:process.env});
process.exitCode=result.status??1;
