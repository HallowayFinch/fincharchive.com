export const archiveOfficeAssets = {
  background: {
    id: 'BP-001',
    path: '/assets/archive-office/background/bp-001.webp',
  },

  interactive: [
    {
      id: 'AO-101',
      name: 'CASE FOLDER',
      path: '/assets/archive-office/interactive/ao-101-folder.webp',
      status: 'INDEXED',
      target: '/logs/',
    },
    {
      id: 'AO-102',
      name: 'MAGNETIC AUDIO RECORDER',
      path: '/assets/archive-office/interactive/ao-102-recorder.webp',
      status: 'OPERATIONAL',
      target: '/t/',
    },
    {
      id: 'AO-103',
      name: 'FIELD NOTEBOOK',
      path: '/assets/archive-office/interactive/ao-103-notebook.webp',
      status: 'ACTIVE',
      target: '/field-notes/',
    },
    {
      id: 'AO-104',
      name: 'PHOTOGRAPH STACK',
      path: '/assets/archive-office/interactive/ao-104-photographs.webp',
      status: 'INDEXED',
      target: '/timeline/',
    },
  ],

  ambient: [
    {
      id: 'AO-105',
      name: 'Coffee Mug',
      path: '/assets/archive-office/ambient/ao-105-mug.webp',
    },
    {
      id: 'AO-106',
      name: 'Keys',
      path: '/assets/archive-office/ambient/ao-106-keys.webp',
    },
    {
      id: 'AO-107',
      name: 'Pencil Cup',
      path: '/assets/archive-office/ambient/ao-107-pencilcup.webp',
    },
  ],

  ephemeral: [],
};
