interface PlayerProps {
  runData: any
}

export default function Player({ runData }: PlayerProps) {
  const videoUrl = runData.artifacts?.video_url
  const images = runData.artifacts?.images || []

  return (
    <div className="player">
      <h2>생성 완료!</h2>

      {videoUrl && (
        <div className="video-container">
          <video controls className="video-player">
            <source src={videoUrl} type="video/mp4" />
            브라우저가 비디오를 지원하지 않습니다.
          </video>
          <a href={videoUrl} download className="btn-download">
            다운로드
          </a>
        </div>
      )}

      {images.length > 0 && (
        <div className="thumbnails">
          <h3>생성된 이미지</h3>
          <div className="thumbnail-grid">
            {images.map((img: any, idx: number) => (
              <div key={idx} className="thumbnail">
                <img src={img.image_url} alt={`Scene ${img.scene_id}`} />
                <p>{img.scene_id} - {img.slot_id}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="metadata">
        <h3>메타데이터</h3>
        <pre>{JSON.stringify(runData.artifacts, null, 2)}</pre>
      </div>
    </div>
  )
}
