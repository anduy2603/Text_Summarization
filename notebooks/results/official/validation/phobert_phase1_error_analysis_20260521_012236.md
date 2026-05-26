# PHOBERT-EXTRACTIVE Short Error Analysis

- Official `top_k`: `2`
- Sample size: `200`
- Mean ROUGE-1/2/L: `0.4759` / `0.2120` / `0.2955`
- Mean compression ratio: `0.1734`
- Mean repetition rate: `0.0401`

## Failure Cases (3 lowest ROUGE-L)
### Case 1 - guid 15460
- ROUGE-1/2/L: `0.1899` / `0.1014` / `0.1293`
- Article snippet: Xin Thủ_tướng cho_biết thông_điệp của Việt_Nam tại Hội_nghị lần này ? Thủ_tướng Nguyễn_Xuân_Phúc : Trước_hết , chúng_tôi hoan_nghênh nỗ_lực của Thái_Lan , nước Chủ_tịch ASEAN 2019 thúc_đẩy hợp_tác trên tinh_thần Chủ_đề của năm 2019 về " Tăng_cường đối_tác vì sự bền_vững , " hướng đến Cộng_đồng ASEAN phát_triển vững_mạnh trên cả 3 trụ_cột , hướng đến người_dân và lấy người_dân làm trung_tâm . Việt_Nam ủng_hộ và sẽ tích_cực tham_gia triển_khai các sáng_kiến của Thái_Lan , trong đó có tăng_cường ph
- Reference summary: Nhân_dịp tham_dự Hội_nghị cấp cao ASEAN lần thứ 34 tại Bangkok ( Thái_Lan ) trong hai ngày 22-23/6 , Thủ_tướng Chính_phủ Nguyễn_Xuân_Phúc đã trả_lời phỏng_vấn báo The_Nation ( Thái_Lan ) .
- Predicted summary: Thủ_tướng Nguyễn_Xuân_Phúc : Trong bối_cảnh căng_thẳng thương_mại và chủ_nghĩa bảo_hộ gia_tăng mạnh_mẽ , cùng với việc Hiệp_định Đối_tác toàn_diện và tiến_bộ xuyên Thái_Bình_Dương CPTPP ( liên_quan đến 4 nước ASEAN ) được triển_khai từ đầu năm 2019 , việc thúc_đẩy đàm_phán RCEP sẽ có ý_nghĩa hết_sức quan_trọng , tạo động_lực mới thúc_đẩy liên_kết kinh_tế đa_phương dựa trên luật_lệ và tự_do_hoá thương_mại tại châu_Á - Thái_Bình_Dương , qua đó góp_phần duy_trì vai_trò của châu_Á - Thái_Bình_Dương 

### Case 2 - guid 18826
- ROUGE-1/2/L: `0.1879` / `0.0743` / `0.1409`
- Article snippet: Buổi giao_lưu giữa dịch_giả Nguyễn_Bá_Quỳnh với bạn_đọc tại Đường sách TP. HCM sáng 18-1 nhằm giới_thiệu quyển sách Nhấn nút tái_tạo - tác_giả Satya_Nadella , CEO của Microsoft - là cuộc chuyện_trò mang nhiều gợi_mở cho cái nhìn về công_nghệ ứng_dụng trong tương_lai . Sách được chú_ý không_chỉ bởi nó được một trong 3 CEO lừng_danh của Microsoft viết ra , tất_nhiên , vai_trò của Satya trong việc định_hướng cho Microsoft để có_thể chuyển_đổi cục_diện của tập_đoàn này khi lần_lượt các đối_thủ đang 
- Reference summary: Một cuốn sách thú_vị về ' hành_trình tìm lại linh_hồn cho Microsoft ' vừa ra_mắt bạn_đọc .
- Predicted summary: Nghệ_thuật và tầm nhìn của ông trong thế_giới công_nghệ được trình_bày như những câu_chuyện gần_gũi , có_thể phù_hợp với " khẩu_vị " nhiều người , miễn_là có quan_tâm đến sự phát_triển của công_nghệ đang làm thay_đổi thế_giới như_thế_nào Tâm_đắc với tác_phẩm , Nguyễn_Bá_Quỳnh - nguyên Giám_đốc khối khách_hàng Chính_phủ và doanh_nghiệp Nhà_nước của Microsoft - cho_rằng nhà_xuất_bản Trẻ ấn_hành quyển sách này thật đúng lúc , nhất_là khi mọi người đang nhắc nhiều đến cuộc cách_mạng công_nghệ 4.0 . 

### Case 3 - guid 10397
- ROUGE-1/2/L: `0.3308` / `0.0916` / `0.1654`
- Article snippet: Một nữ cổ_động_viên Nga vẽ cờ lên_mặt để cổ_vũ đội nhà trong trận gặp Ai_Cập hôm 19/6 . Ảnh : AFP " Những phụ_nữ có được gen bóng_đá tốt nhất sẽ thúc_đẩy thành_công của đội_tuyển Nga trong các thế_hệ kế_tiếp " , BBC dẫn quảng_cáo của chi_nhánh Burger_King tại Nga viết . Ngoài phần_thưởng tiền_mặt 3 triệu ruble ( 47.000 USD ) , những người đáp_ứng tiêu_chí còn được ăn hamburger miễn_phí trọn đời . Tuy_nhiên , quảng_cáo trên nhanh_chóng bị người dùng mạng lên_án là phân_biệt giới_tính và hạ thấp p
- Reference summary: Chuỗi cửa hàng Burger_King phải xin lỗi sau khi treo thưởng 3 triệu ruble cho phụ nữ nào có con với một cầu thủ tham dự World_Cup .
- Predicted summary: Không_chỉ trong quảng_cáo trên , phụ_nữ Nga cũng đang bị mô_tả như những thợ_săn đàn_ông trên nhiều kênh truyền_thông . Trong một video trên YouTube , người dẫn_chương_trình truyền_hình còn cho_hay " hàng trăm , hàng nghìn cô_gái quyến_rũ đang đổ về Moskva " với hy_vọng gặp các fan bóng_đá nước_ngoài .
