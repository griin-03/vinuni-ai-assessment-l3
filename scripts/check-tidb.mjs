import {loadDatabaseEnv} from './prisma-env.mjs';
import {PrismaClient} from '@prisma/client';

let prisma;
try{
  const url=loadDatabaseEnv();
  prisma=new PrismaClient({log:[]});
  const [info]=await prisma.$queryRaw`SELECT DATABASE() AS database_name, VERSION() AS server_version, 1 AS connection_ok`;
  const tls=await prisma.$queryRaw`SHOW STATUS LIKE 'Ssl_cipher'`;
  const cipher=tls.find(row=>String(row.Variable_name??row.variable_name).toLowerCase()==='ssl_cipher');
  const tlsActive=Boolean(cipher?.Value??cipher?.value);
  if(!tlsActive)throw new Error('TLS_NOT_ACTIVE');
  const [count]=await prisma.$queryRaw`SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = DATABASE()`;
  console.log(JSON.stringify({connected:Number(info.connection_ok)===1,database:info.database_name,tls:true,configuredTLS:url.searchParams.get('sslaccept'),tableCount:Number(count.table_count),mode:'read_only_connection_check',workspaceRuntime:'python_sqlite',schemaApplied:false},null,2));
}catch(error){
  // Connection errors can contain connection details. Print only a safe code.
  console.error('TiDB connection check failed: '+(error.code|| (error.message==='TLS_NOT_ACTIVE'?'TLS_NOT_ACTIVE':'CONFIG_OR_CONNECTION_ERROR')));
  process.exitCode=1;
}finally{
  if(prisma)await prisma.$disconnect();
}
