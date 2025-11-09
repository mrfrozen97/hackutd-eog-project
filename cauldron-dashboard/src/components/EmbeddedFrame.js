import React from 'react';

/**
 * Simple reusable iframe wrapper.
 *
 * Props:
 * - src (string): URL to embed (required)
 * - title (string): Accessible title for the frame
 * - height (number|string): Height (px number or CSS string). Default 600
 * - allow (string): allow attribute (e.g., 'fullscreen')
 * - className (string): optional container class
 * - style (object): inline styles for container
 * - frameStyle (object): inline styles for the iframe itself
 * - allowFullScreen (boolean): allow fullscreen
 * - sandbox (string): sandbox attribute if needed
 * - referrerPolicy (string): referrer policy; default 'no-referrer'
 */
const EmbeddedFrame = ({
  src,
  title = 'Embedded View',
  height = 600,
  allow = 'fullscreen',
  className = '',
  style = {},
  frameStyle = {},
  allowFullScreen = true,
  sandbox,
  referrerPolicy = 'no-referrer',
}) => {
  const containerStyles = {
    border: '1px solid #e0e0e0',
    borderRadius: 8,
    overflow: 'hidden',
    background: '#fff',
    marginBottom: 24, // Added spacing below the embedded frame
    ...style,
  };

  const iframeStyles = {
    width: '100%',
    height: typeof height === 'number' ? `${height}px` : height,
    border: 0,
    display: 'block',
    ...frameStyle,
  };

  return (
    <div className={className} style={containerStyles}>
      <iframe src="http://localhost:5601/app/dashboards#/view/ad89797a-7dc3-4d7f-8afa-067bc8536607?embed=true&_g=%28refreshInterval%3A%28pause%3A%21t%2Cvalue%3A10000%29%2Ctime%3A%28from%3Anow-7h%2Cto%3Anow%29%29&show-time-filter=true" height="1000" width="1400"></iframe>
    </div>
  );
};

export default EmbeddedFrame;
