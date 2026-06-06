/**
 * Chuyển thông báo lỗi kỹ thuật (API / network) sang tiếng Việt dễ hiểu.
 */
export function toFriendlyError(raw: string): string {
  const s = raw.trim();
  const lower = s.toLowerCase();

  if (
    lower.includes("failed to fetch") ||
    lower.includes("cannot connect") ||
    lower.includes("networkerror") ||
    lower.includes("network error")
  ) {
    return "Không kết nối được máy chủ. Hãy kiểm tra backend đang chạy (API) rồi thử lại.";
  }

  if (lower.includes("timeout") || lower.includes("timed out")) {
    return "Hết thời gian xử lý. Thử lại với văn bản ngắn hơn hoặc tệp nhỏ hơn.";
  }

  if (lower.includes("422") || lower.includes("unprocessable")) {
    if (
      lower.includes("no extractable text") ||
      lower.includes("không chứa văn bản") ||
      lower.includes("text layer") ||
      lower.includes("lớp văn bản")
    ) {
      return (
        "PDF không có văn bản đọc được (thường gặp với bản scan ảnh hoặc PDF chỉ có hình). " +
        "Hãy dùng file TXT/DOCX hoặc bản PDF có lớp văn bản."
      );
    }
    if (lower.includes("url") || lower.includes("fetch")) {
      return "Không trích được nội dung từ link. Kiểm tra URL hoặc thử trang khác.";
    }
    if (lower.includes("empty") || lower.includes("short") || lower.includes("minimum")) {
      return "Nội dung quá ngắn hoặc trống sau khi đọc tệp. Hãy dùng bản văn bản đầy đủ hơn.";
    }
    return "Không đọc được nội dung. Kiểm tra tệp (TXT/DOCX/PDF) hoặc link bài báo.";
  }

  if (lower.includes("400") || lower.includes("validation")) {
    return "Dữ liệu không hợp lệ. Chỉ hỗ trợ TXT, DOCX, PDF hoặc link http(s).";
  }

  if (lower.includes("413") || lower.includes("too large") || lower.includes("max_file")) {
    return "Tệp quá lớn. Hãy chọn tệp nhỏ hơn hoặc cắt bớt nội dung.";
  }

  if (lower.includes("415") || lower.includes("unsupported") || lower.includes("extension")) {
    return "Định dạng tệp không được hỗ trợ. Chỉ dùng .txt, .docx hoặc .pdf.";
  }

  if (lower.includes("501") || lower.includes("not ready") || lower.includes("phobert")) {
    return "Engine tóm tắt chưa sẵn sàng trên máy chủ. Thử lại sau hoặc dùng cài đặt mặc định.";
  }

  if (lower.includes("500") || lower.includes("internal server")) {
    return "Lỗi máy chủ khi xử lý. Thử lại sau vài giây.";
  }

  if (s.length > 180) {
    return "Đã xảy ra lỗi khi tóm tắt. Vui lòng thử lại hoặc đổi tệp / link khác.";
  }

  return s;
}
