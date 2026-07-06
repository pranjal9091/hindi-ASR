/**
 * History manager service to auto-save and retrieve transcription sessions locally using localStorage.
 */

const HISTORY_KEY = "hindi_asr_history";

export function autoSaveTranscript(duration, transcript, words, segments, language = "hi", processingTime = 0, confidence = 0.95, clinical = null) {
  const item = {
    id: "hist_" + Date.now() + "_" + Math.random().toString(36).substr(2, 5),
    date: new Date().toISOString(),
    duration,
    transcript,
    words,
    segments,
    language,
    processingTime,
    confidence,
    clinical
  };
  try {
    const current = getHistoryItems();
    current.unshift(item);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(current));
    return item;
  } catch (err) {
    console.error("Failed to auto-save transcription session: ", err);
    return null;
  }
}

export function getHistoryItems() {
  try {
    const data = localStorage.getItem(HISTORY_KEY);
    return data ? JSON.parse(data) : [];
  } catch (err) {
    console.error("Failed to retrieve local transcription history: ", err);
    return [];
  }
}

export function deleteHistoryItem(id) {
  try {
    const current = getHistoryItems();
    const filtered = current.filter(item => item.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
    return true;
  } catch (err) {
    console.error("Failed to delete local history item: ", err);
    return false;
  }
}
