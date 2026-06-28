import { archiveOfficeAssets } from '../../assets/archive-office';

export const archiveOffice = {
  id: 'archive-office',
  internalName: 'Archive Office',
  publicName: 'The Archive',
  time: '22:22',
  camera: {
    angle: 'three-quarter-overhead',
    degrees: 25,
    lens: '35mm equivalent',
    position: 'standing at desk',
  },
  lighting: {
    primary: 'warm tungsten desk lamp',
    secondary: 'cool moonlight from left window',
    overhead: false,
  },
  assets: {
    background: archiveOfficeAssets.background.path,
    objectsPath: '/assets/archive-office/objects/',
  },
  environment: [
    'dark walnut desk',
    'desk lamp',
    'window',
    'corkboard',
    'shelves',
    'filing cabinet',
    'analog wall clock stopped at 10:22',
  ],
  interactiveProps: [
    { id: 'case-files', label: 'Case Files', href: '/logs/' },
    { id: 'field-notes', label: 'Field Notes', href: '/field-notes/' },
    { id: 'recorder', label: 'Recorder', href: '/t/' },
    { id: 'photographs', label: 'Photographs', href: '/timeline/' },
    { id: 'keys', label: 'Keys', href: null },
  ],
};
