import { archiveOfficeAssets } from '../../assets/archive-office';
import type { PresenceSystem } from '../../models/scene';

const archiveOfficePresence = [
  {
    id: 'window-rain',
    kind: 'rain',
    intensity: 'low',
    x: 66.8,
    y: 0,
    width: 24.6,
    height: 43.5,
  },
  {
    id: 'lamp-atmosphere',
    kind: 'dust',
    intensity: 'low',
    x: 0.5,
    y: 18,
    width: 31,
    height: 56,
  },
  {
    id: 'lamp-instability',
    kind: 'lamp-instability',
    intensity: 'low',
    x: 0,
    y: 18,
    width: 34,
    height: 62,
  },
] satisfies PresenceSystem[];

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
  presence: archiveOfficePresence,
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
