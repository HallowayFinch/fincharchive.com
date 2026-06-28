import { getLogs } from '../logs';
import { getFieldNotes } from '../field-notes';

export async function getTimeline() {
  const [logs, fieldNotes] = await Promise.all([
    getLogs(),
    getFieldNotes(),
  ]);

  const records = [
    ...logs.map((r) => ({ ...r, type: 'log' })),
    ...fieldNotes.map((r) => ({ ...r, type: 'field-note' })),
  ];

  return records.sort(
    (a, b) =>
      new Date(b.date).getTime() -
      new Date(a.date).getTime()
  );
}
