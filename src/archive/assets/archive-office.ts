export const archiveOfficeAssets = {
  background: {
    id: 'BP-001',
    path: '/assets/archive-office/background/bp-001.webp',
    productionStage: 'first-pass AP-001 obstruction-muted plate',
    cleanup: 'Manual background cleanup required to remove movable desk materials cleanly and produce a true BP-001 plate.',
  },

  interactive: [
    {
      id: 'AO-101',
      name: 'CASE FOLDER',
      path: '/assets/archive-office/interactive/ao-101-folder.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup required around the folder stack.',
      status: 'INDEXED',
      target: '/logs/',
    },
    {
      id: 'AO-102',
      name: 'MAGNETIC AUDIO RECORDER',
      path: '/assets/archive-office/interactive/ao-102-recorder.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup recommended around reels and housing.',
      status: 'OPERATIONAL',
      target: '/t/',
    },
    {
      id: 'AO-103',
      name: 'FIELD NOTEBOOK',
      path: '/assets/archive-office/interactive/ao-103-notebook.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup recommended around notebook corners and pen.',
      status: 'ACTIVE',
      target: '/field-notes/',
    },
    {
      id: 'AO-104',
      name: 'PHOTOGRAPH STACK',
      path: '/assets/archive-office/interactive/ao-104-photographs.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup required around the photo stack.',
      status: 'INDEXED',
      target: '/timeline/',
    },
  ],

  ambient: [
    {
      id: 'AO-105',
      name: 'COFFEE MUG',
      path: '/assets/archive-office/ambient/ao-105-mug.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup recommended around handle and rim.',
      status: 'AMBIENT',
    },
    {
      id: 'AO-106',
      name: 'KEYS',
      path: '/assets/archive-office/ambient/ao-106-keys.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup required around key rings.',
      status: 'AMBIENT',
    },
    {
      id: 'AO-107',
      name: 'DESK LAMP',
      path: '/assets/archive-office/ambient/ao-107-desk-lamp.webp',
      productionStage: 'first-pass AP-001 masked crop',
      cleanup: 'Manual transparent-edge cleanup required; confirm whether AO-107 should remain desk lamp or return to cassette in the registry.',
      status: 'AMBIENT',
    },
  ],

  ephemeral: [],
};
