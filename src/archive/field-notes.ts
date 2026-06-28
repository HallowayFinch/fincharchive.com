import {
  getCollection,
  getCollectionEntry,
  getCollectionSlugs,
  type ArchiveEntry,
} from './loader';

const fieldNotes = {
  directory: '_field-notes',
  permalinkBase: 'field-notes',
};

export type FieldNote = ArchiveEntry;

export function getFieldNoteSlugs() {
  return getCollectionSlugs(fieldNotes.directory);
}

export function getFieldNote(slug: string) {
  return getCollectionEntry(slug, fieldNotes);
}

export function getFieldNotes() {
  return getCollection(fieldNotes);
}
