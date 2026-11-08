import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

export function loadDatabaseEnv(){
  const local=fileURLToPath(new URL('../.env.local',import.meta.url));
  if(existsSync(local))process.loadEnvFile(local);
  if(!process.env.DATABASE_URL)throw new Error('DATABASE_URL chưa được cấu hình.');
  const url=new URL(process.env.DATABASE_URL);
  if(url.protocol!=='mysql:')throw new Error('TiDB cần connection URL dùng mysql.');
  if(url.searchParams.get('sslaccept')!=='strict')throw new Error('Kết nối TiDB phải dùng sslaccept=strict.');
  return url;
}
