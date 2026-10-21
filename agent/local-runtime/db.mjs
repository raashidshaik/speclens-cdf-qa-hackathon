import {PGlite} from '@electric-sql/pglite';
import {PGLiteSocketServer} from '@electric-sql/pglite-socket';
import {readFileSync} from 'node:fs';
const db=await PGlite.create();
await db.exec(readFileSync('../test-website/database/migrations/001_create_schema.sql','utf8'));
await db.exec(readFileSync('../test-website/database/seed.sql','utf8'));
const server=new PGLiteSocketServer({db,host:'127.0.0.1',port:5432,maxConnections:10});
await server.start(); console.log('Seeded local PGlite runtime at 127.0.0.1:5432');
