/** Visual tones in the GRIT palette. Colour is never the only signal: every toned element
 * also carries text. TONE_CLASSES tint a surface. */
export type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'review';

export const TONE_CLASSES: Record<Tone, string> = {
  neutral: 'bg-sand text-ink border-line-strong',
  info: 'bg-[#eaf0ff] text-[#1d3f9a] border-grit-blue-strong',
  success: 'bg-[#e6f5ec] text-[#14603a] border-grit-green',
  warning: 'bg-[#fff8cc] text-[#4d3f00] border-[#b9a41a]',
  danger: 'bg-[#fdecec] text-[#94262b] border-grit-red-strong',
  review: 'bg-[#f2eaf9] text-[#55307a] border-grit-purple',
};

export function asTone(value: string): Tone {
  return value in TONE_CLASSES ? (value as Tone) : 'neutral';
}
