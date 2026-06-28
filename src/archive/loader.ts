import fs from 'node:fs/promises';
import path from 'node:path';

export type ArchiveEntry = {
  slug: string;
  title: string;
  date: string;
  permalink: string;
  body: string;
};

type CollectionOptions = {
  directory: string;
  permalinkBase: string;
  titlePrefix?: string;
};

function readField(frontmatter: string, key: string) {
  const quoted = frontmatter.match(new RegExp(`^${key}:\\s*"([^"]+)"`, 'm'));
  if (quoted) return quoted[1];

  const unquoted = frontmatter.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
  return unquoted?.[1]?.trim() ?? '';
}

export async function getCollectionSlugs(directory: string) {
  const collectionDir = path.join(process.cwd(), directory);
  const files = await fs.readdir(collectionDir);

  return files
    .filter((file) => file.endsWith('.md'))
    .map((file) => file.replace(/\.md$/, ''))
    .sort();
}

export async function getCollectionEntry(
  slug: string,
  options: CollectionOptions
): Promise<ArchiveEntry> {
  const collectionDir = path.join(process.cwd(), options.directory);
  const file = await fs.readFile(path.join(collectionDir, `${slug}.md`), 'utf-8');
  const [, frontmatter = '', body = ''] = file.split('---');

  const title = readField(frontmatter, 'title') || `${options.titlePrefix ?? ''}${slug}`;

  return {
    slug,
    title,
    date: readField(frontmatter, 'date'),
    permalink: readField(frontmatter, 'permalink') || `/${options.permalinkBase}/${slug}/`,
    body: body.trim(),
  };
}

export async function getCollection(options: CollectionOptions) {
  const slugs = await getCollectionSlugs(options.directory);
  const entries = await Promise.all(
    slugs.map((slug) => getCollectionEntry(slug, options))
  );

  return entries.sort((a, b) => Date.parse(b.date) - Date.parse(a.date));
}
