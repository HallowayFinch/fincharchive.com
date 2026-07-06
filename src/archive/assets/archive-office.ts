export const archiveOfficeAssets = {
  background: {
    id: 'BP-001',
    path: '/assets/archive-office/background/bp-001.webp',
    productionStage: 'approved clean Archive Office room and desk plate',
    cleanup: 'Runtime QA should confirm object-layer placement, hover/focus affordance, and Presence fit over the clean desk surface.',
  },

  interactive: [
    {
      id: 'AO-101',
      name: 'CASE FOLDER',
      path: '/assets/archive-office/interactive/ao-101-folder.webp',
      productionStage: 'HF-0.4 final-approved transparent runtime layer',
      cleanup: 'Runtime QA should confirm front-left placement and tooltip containment.',
      status: 'INDEXED',
      target: '/logs/',
    },
    {
      id: 'AO-102',
      name: 'MAGNETIC AUDIO RECORDER',
      path: '/assets/archive-office/interactive/ao-102-recorder.webp',
      productionStage: 'HF-0.4 final-approved transparent runtime layer with tightened canvas',
      cleanup: 'Runtime QA should confirm desk grounding and spacing from the coffee mug.',
      status: 'OPERATIONAL',
      target: '/t/',
    },
    {
      id: 'AO-103',
      name: 'FIELD NOTEBOOK',
      path: '/assets/archive-office/interactive/ao-103-notebook.webp',
      productionStage: 'HF-0.4 final-approved transparent runtime layer with tightened canvas',
      cleanup: 'Runtime QA should confirm left-center desk grounding.',
      status: 'ACTIVE',
      target: '/field-notes/',
    },
    {
      id: 'AO-104',
      name: 'PHOTOGRAPH STACK',
      path: '/assets/archive-office/interactive/ao-104-photographs.webp',
      productionStage: 'HF-0.4 final-approved transparent runtime layer',
      cleanup: 'Runtime QA should confirm front-right placement and tooltip containment.',
      status: 'INDEXED',
      target: '/timeline/',
    },
  ],

  ambient: [
    {
      id: 'AO-105',
      name: 'COFFEE MUG',
      path: '/assets/archive-office/ambient/ao-105-mug.webp',
      productionStage: 'HF-0.4 final-approved transparent ambient layer with tightened canvas',
      cleanup: 'Runtime QA should confirm the mug remains clear of the recorder.',
      status: 'AMBIENT',
    },
    {
      id: 'AO-106',
      name: 'KEYS',
      path: '/assets/archive-office/ambient/ao-106-keys.webp',
      productionStage: 'HF-0.4 final-approved transparent ambient layer with tightened canvas',
      cleanup: 'Runtime QA should confirm the keys remain naturally seated front-center.',
      status: 'AMBIENT',
    },
    {
      id: 'AO-107',
      name: 'DESK LAMP',
      path: '/assets/archive-office/ambient/ao-107-desk-lamp.webp',
      productionStage: 'HF-0.4 final-approved ambient asset retained for future lamp-layer review',
      cleanup: 'Current runtime uses the background lamp treatment; do not render AO-107 separately without visual QA.',
      status: 'AMBIENT',
    },
  ],

  ephemeral: [],
};
