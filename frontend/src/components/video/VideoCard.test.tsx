import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { VideoResponse } from "@/types/api";

import { VideoCard } from "./VideoCard";

function makeVideo(overrides: Partial<VideoResponse> = {}): VideoResponse {
  return {
    id: "1",
    youtube_video_id: "dQw4w9WgXcQ",
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "Sample Video",
    description: null,
    channel_name: "Sample Channel",
    channel_id: "UC123",
    thumbnail_url: "https://img.example.com/thumb.jpg",
    duration_seconds: 3725,
    view_count: 1500000,
    upload_date: "2024-01-15",
    original_language: "en",
    created_at: "2024-01-15T00:00:00Z",
    ...overrides,
  };
}

describe("VideoCard", () => {
  it("renders title and channel name", () => {
    render(<VideoCard video={makeVideo()} />);
    expect(screen.getByText("Sample Video")).toBeInTheDocument();
    expect(screen.getByText(/Sample Channel/)).toBeInTheDocument();
  });

  it("formats duration as h:mm:ss for videos over an hour", () => {
    render(<VideoCard video={makeVideo({ duration_seconds: 3725 })} />);
    expect(screen.getByText(/1:02:05/)).toBeInTheDocument();
  });

  it("formats duration as m:ss for videos under an hour", () => {
    render(<VideoCard video={makeVideo({ duration_seconds: 125 })} />);
    expect(screen.getByText(/2:05/)).toBeInTheDocument();
  });

  it("formats large view counts with an M suffix", () => {
    render(<VideoCard video={makeVideo({ view_count: 1500000 })} />);
    expect(screen.getByText(/1\.5M views/)).toBeInTheDocument();
  });

  it("formats mid-size view counts with a K suffix", () => {
    render(<VideoCard video={makeVideo({ view_count: 2500 })} />);
    expect(screen.getByText(/2\.5K views/)).toBeInTheDocument();
  });

  it("does not render a thumbnail image when none is provided", () => {
    render(<VideoCard video={makeVideo({ thumbnail_url: null })} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
