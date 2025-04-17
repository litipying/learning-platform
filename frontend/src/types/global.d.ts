declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}

declare module 'animejs' {
  const anime: any;
  export default anime;
} 