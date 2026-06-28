import {
  getCollection,
  getCollectionEntry,
  getCollectionSlugs,
  type ArchiveEntry,
} from './loader';

const logs = {
  directory: '_logs',
  permalinkBase: 'logs',
};

export type ArchiveRecord = ArchiveEntry;

export function getLogSlugs() {
  return getCollectionSlugs(logs.directory);
}

export function getLog(slug: string) {
  return getCollectionEntry(slug, logs);
}

export function getLogs() {
  return getCollection(logs);
}
