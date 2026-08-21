import { defineConfig, env } from '@prisma/config';

export default defineConfig({
  schema: './prisma/postgresql-schema.prisma',
  datasource: {
    url: env('DATABASE_CONNECTION_URI'),
  },
});
