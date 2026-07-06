import { BACKEND_URL } from "../config";

/**
 * Sends an audio Blob to the FastAPI ASR backend for transcription.
 * @param {Blob} audioBlob - The recorded audio data
 * @param {string} extension - The audio file extension (e.g. webm, wav, mp4)
 * @returns {Promise<object>} The JSON response payload containing success, transcript, segments, etc.
 */
export async function transcribeAudioFile(audioBlob, extension = "webm") {
  const formData = new FormData();
  formData.append("file", audioBlob, `recording.${extension}`);

  const response = await fetch(`${BACKEND_URL}/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Server returned error status: ${response.status}`);
  }

  return response.json();
}
