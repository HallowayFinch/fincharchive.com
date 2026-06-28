import fs from 'node:fs/promises';
import path from 'node:path';

const logsDir = path.join(process.cwd(), '_logs');

export type ArchiveRecord = {
  slug: string;
  title: string;
  date: string;
  permalink: string;
  body: string;
};

export async function getLogSlugs() {
  const files = await fs.readdir(logsDir);
  return files
    .filter((file) => file.endsWith('.md'))
    .map((file) => file.replace(/\.md$/, ''))
    .sort();
}

export async function getLog(slug: string): Promise<ArchiveRecord> {
  const file = await fs.readFile(path.join(logsDir, `${slug}.md`), 'utf-8');
  const [, frontmatter = '', body = ''] = file.split('---');

  return {
    slug,
    title: frontmatter.match(/title:\s*"([^"]+)"/)?.[1] ?? slug,
    date: frontmatter.match(/date:\s*"([^"]+)"/)?.[1] ?? '',
    permalink: frontmatter.match(/permalink:\s*"([^"]+)"/)?.[1] ?? `/logs/${slug}/`,
    body: body.trim(),
  };
}

export async function getLogs() {
  const slugs = await getLogSlugs();
  const logs = await Promise.all(slugs.map(getLog));

  return logs.sort((a, b) => Date.parse(b.date) - Date.parse(a.date));
}
