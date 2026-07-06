/**
 * Automatically restores Hindi punctuation, detects paragraphs based on pauses,
 * and compiles the word timeline from raw Whisper segments.
 * @param {Array} segments - Raw segment list from backend response
 * @returns {object} Object containing processedText string and wordTimeline array
 */
export function processASRSegments(segments) {
  const words = [];
  
  // 1. Flatten all words and compute metrics
  segments.forEach(seg => {
    if (seg.words && seg.words.length > 0) {
      seg.words.forEach(w => {
        words.push({
          text: w.word.trim(),
          start: w.start,
          end: w.end,
          confidence: w.probability
        });
      });
    } else {
      // Fallback: split segment text
      const segWords = seg.text.split(/\s+/).filter(Boolean);
      const segWordCount = segWords.length;
      const segDuration = seg.end - seg.start;
      segWords.forEach((word, idx) => {
        words.push({
          text: word.trim(),
          start: seg.start + (idx / segWordCount) * segDuration,
          end: seg.start + ((idx + 1) / segWordCount) * segDuration,
          confidence: Math.exp(seg.avg_logprob || -0.05)
        });
      });
    }
  });

  if (words.length === 0) return { processedText: "", wordTimeline: [] };

  const questionWords = ["क्या", "क्यों", "क्यूं", "कब", "कैसे", "कहाँ", "कहा", "किधर", "कौन", "किसने", "किस", "कितना", "कितने"];
  const processedWords = [];

  for (let i = 0; i < words.length; i++) {
    const current = { ...words[i] };
    const prev = processedWords[processedWords.length - 1];

    // 2. Hindi Punctuation / Sentence Restoration based on time gaps
    if (prev) {
      const gap = current.start - prev.end;

      // Check if there is a gap indicating a pause
      if (gap > 1.2) {
        const lastChar = prev.text[prev.text.length - 1];
        const isPunctuated = ["।", "?", ",", "!", "."].includes(lastChar);
        
        if (!isPunctuated) {
          // Check if previous sentence segment had question words
          let isQuestion = false;
          // Look back up to 6 words to see if it contains a question word
          for (let j = Math.max(0, processedWords.length - 6); j < processedWords.length; j++) {
            if (questionWords.some(qw => processedWords[j].text.includes(qw))) {
              isQuestion = true;
              break;
            }
          }

          if (isQuestion) {
            prev.text += "?";
          } else {
            prev.text += "।";
          }
        }
      }
    }

    processedWords.push(current);
  }

  // Ensure the very last word has a full stop or question mark
  if (processedWords.length > 0) {
    const lastWord = processedWords[processedWords.length - 1];
    const lastChar = lastWord.text[lastWord.text.length - 1];
    if (!["।", "?", ",", "!", "."].includes(lastChar)) {
      lastWord.text += "।";
    }
  }

  // 3. Paragraph Detection based on long pauses (>2.5s)
  let processedText = "";
  for (let i = 0; i < processedWords.length; i++) {
    const current = processedWords[i];
    const prev = processedWords[i - 1];

    if (prev && (current.start - prev.end > 2.5)) {
      processedText += "\n\n" + current.text;
    } else {
      if (processedText === "") {
        processedText = current.text;
      } else {
        processedText += " " + current.text;
      }
    }
  }

  return {
    processedText,
    wordTimeline: processedWords
  };
}
