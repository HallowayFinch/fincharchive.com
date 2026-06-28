import { room01 } from './room01';

export const deskScene = {
  id: 'scene-0001',
  room: room01,
  name: room01.publicName,
  objects: [
    {
      id: 'case-files',
      label: 'Case Files',
      href: '/logs/',
      x: 58,
      y: 38,
      width: 22,
      height: 24,
    },
    {
      id: 'field-notes',
      label: 'Field Notes',
      href: '/field-notes/',
      x: 18,
      y: 34,
      width: 18,
      height: 22,
    },
    {
      id: 'recorder',
      label: 'Recorder',
      href: '/t/',
      x: 45,
      y: 18,
      width: 18,
      height: 20,
    },
    {
      id: 'photographs',
      label: 'Photographs',
      href: '/timeline/',
      x: 38,
      y: 58,
      width: 20,
      height: 16,
    },
  ],
};
