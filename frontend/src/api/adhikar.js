// src/api/adhikar.js — API client for Adhikar backend

const BASE_URL = "http://127.0.0.1:8000";

export async function queryAdhikar(query, language = null) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, language }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Something went wrong");
  }
  return response.json();
}

export async function getLanguages() {
  const response = await fetch(`${BASE_URL}/languages`);
  return response.json();
}

export async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");

  const response = await fetch(`${BASE_URL}/transcribe`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Transcription failed");
  }
  return response.json(); // { text, language, confidence }
}
