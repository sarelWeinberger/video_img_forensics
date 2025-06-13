/*
 * @(#)JPEGMarkerInputStream.java
 *
 * $Date: 2014-03-13 04:15:48 -0400 (Thu, 13 Mar 2014) $
 *
 * Copyright (c) 2011 by Jeremy Wood.
 * All rights reserved.
 *
 * The copyright of this software is owned by Jeremy Wood. 
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * Jeremy Wood. For details see accompanying license terms.
 * 
 * This software is probably, but not necessarily, discussed here:
 * https://javagraphics.java.net/
 * 
 * That site should also contain the most recent official version
 * of this software.  (See the SVN repository for more details.)
 *
 Modified BSD License

Copyright (c) 2015, Jeremy Wood.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
* The name of the contributors may not be used to endorse or promote products derived from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package gr.iti.mklab.reveal.forensics.util.ThumbnailExtractor.image.jpeg;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;

/** This stream reads discrete sections of a JPEG file.
 * It is modeled after the <code>ZipInputStream</code>:
 * the stream appears to end and no more data will be read
 * as one marker ends.  You have to call <code>getNextMarker()</code>
 * to progress to the next section of the JPEG.
 * <p>This object is designed for and tested against markers
 * that precede the image data.  When the start of scan marker (0xFFDA)
 * is reached: this is when you need to stop using this object.
 * That marker is special because it technically contains
 * a finite amount of data, but once it ends the JPEG image data begins.
 */
class JPEGMarkerInputStream extends InputStream {
	
	protected static final String START_OF_IMAGE_MARKER = "FFD8";
	protected static final String END_OF_IMAGE_MARKER = "FFD9";
	protected static final String APP0_MARKER = "FFE0";
	protected static final String APP1_MARKER = "FFE1";
	protected static final String APP2_MARKER = "FFE2";
	protected static final String APP13_MARKER = "FFED";
	protected static final String COMMENT_MARKER = "FFFE";
	protected static final String DEFINE_QUANTIZATION_MARKER = "FFDB";
	protected static final String BASELINE_MARKER = "FFC0";
	protected static final String DEFINE_HUFFMAN_MARKER = "FFC4";
	
	/** The start of scan marker is tricky.  It technically has a small
	 * number of byte data (12 bytes), but following that header
	 * is all the image data for this JPEG until the end of image marker
	 * is reached.  We can't really accurately predict how much data this
	 * will be, though, so basically when we hit this marker this
	 * input stream is done being useful.
	 * 
	 */
	protected static final String START_OF_SCAN_MARKER = "FFDA";
	
	InputStream in;
	String currentMarker;
	int remainingMarkerLength = 0;
	byte[] scratch = new byte[2];
	boolean reverse = false;
	
	public JPEGMarkerInputStream(InputStream in) {
		this.in = in;
	}
	
	/** Returns the current 4-character marker in uppercase, or null
	 * if this stream hasn't been opened yet or is finished.
	 * <p>For example: a start of image marker will return "FFD8".
	 * 
	 */
	public String getCurrentMarker() {
		return currentMarker;
	}
	
	public String getNextMarker() throws IOException {
		skip(remainingMarkerLength);
		
		remainingMarkerLength = 2;
		if(readFully(scratch,2,reverse)!=2)
			throw new EOFException("EOF reached");
		int i = (scratch[0] & 0xff)*256 + (scratch[1] & 0xff);
		currentMarker = Integer.toString(i, 16).toUpperCase();
		if( START_OF_IMAGE_MARKER.equals(currentMarker) || END_OF_IMAGE_MARKER.equals(currentMarker) ) {
			remainingMarkerLength = 0;
		} else {
			remainingMarkerLength = 2;
			if(readFully(scratch,2,reverse)!=2)
				throw new IOException("EOF reached");
			i = (scratch[0] & 0xff)*256 + (scratch[1] & 0xff);
			remainingMarkerLength = i - 2;
		}
		return currentMarker;
		
	}

	@Override
	public int read() throws IOException {
		if(remainingMarkerLength==0) return -1;
		int returnValue = in.read();
		remainingMarkerLength--;
		return returnValue;
	}

	@Override
	public int read(byte[] b) throws IOException {
		int amountToRead = Math.min(b.length, remainingMarkerLength);
		return read(b, 0, amountToRead);
	}

	@Override
	public int read(byte[] b, int off, int len) throws IOException {
		int amountToRead = Math.min(len, remainingMarkerLength);
		if(amountToRead==0 && len!=0)
			return -1;
		
		int returnValue = in.read(b, off, amountToRead);
		if(returnValue>0) {
			remainingMarkerLength -= returnValue;
		}
		return returnValue;
	}

	@Override
	public long skip(long n) throws IOException {
		return skipFully(n);
	}

	@Override
	public int available() throws IOException {
		int returnValue = super.available();
		return Math.min(returnValue, remainingMarkerLength);
	}

	@Override
	public void close() throws IOException {
		in.close();
	}

	@Override
	public synchronized void mark(int readlimit) {
		throw new UnsupportedOperationException();
	}

	@Override
	public synchronized void reset() throws IOException {
		throw new UnsupportedOperationException();
	}

	@Override
	public boolean markSupported() {
		return false;
	}

	protected int readFully(byte[] dest, int amt) throws IOException {
		return readFully(dest, amt, false);
	}
	
	protected int readFully(byte[] dest, int amt,boolean reverse) throws IOException {
		amt = Math.min(amt, remainingMarkerLength);
		int returnValue = readFully(in, dest, amt, reverse);
		remainingMarkerLength -= returnValue;
		return returnValue;
	}

	protected static int readFully(InputStream in,byte[] dest,int amt,boolean reverse) throws IOException {
		int ctr = 0;
		int t = in.read(dest,ctr,amt-ctr);
		while(t+ctr!=amt && t!=-1) {
			ctr+=t;
			t = in.read(dest,ctr,amt-ctr);
		}
		if(t!=-1)
			ctr+=t;

		if(reverse) {
			t = ctr/2;
			for(int i = 0; i<t; i++) {
				byte k = dest[amt-1-i];
				dest[amt-1-i] = dest[i];
				dest[i] = k;
			}
		}
		return ctr;
	}
	
	protected long skipFully(long amt) throws IOException {
		amt = Math.min(amt, remainingMarkerLength);
		long returnValue = skipFully( in, amt);
		remainingMarkerLength -= returnValue;
		return returnValue;
	}
	
	protected static long skipFully(InputStream in,long amount) throws IOException {
		/** The description of InputStream.skip() is
		 * unfulfilling.  It is perfectly OK for
		 * InputStream.skip() to return zero, but
		 * not necessarily mean EOF.
		 */

		if(amount<0) return 0;
		
		long sum = 0;
		long t = in.skip(amount-sum);
		while(t+sum!=amount) {
			if(t==0) {
				//in.read() has a clear EOF indicator, though:
				t = in.read();
				if(t==-1)
					return sum;
				sum++;
			} else {
				sum+=t;
			}
			t = in.skip(amount-sum);
		}

		return t+sum;
	}
	
	protected static String toString(byte[] array,int length) {
		StringBuffer sb = new StringBuffer();
		for(int a = 0; a<length; a++) {
			sb.append( (char)array[a] );
		}
		return sb.toString();
	}
}
