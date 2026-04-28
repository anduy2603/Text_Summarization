# TEXTRANK Short Error Analysis

- Official `top_k`: `2`
- Sample size: `200`
- Mean ROUGE-1/2/L: `0.4981` / `0.2236` / `0.3205`
- Mean compression ratio: `0.1397`
- Mean repetition rate: `0.0989`

## Failure Cases (3 lowest ROUGE-L)
### Case 1 - guid 18826
- ROUGE-1/2/L: `0.1854` / `0.0733` / `0.1391`
- Article snippet: Buổi giao_lưu giữa dịch_giả Nguyễn_Bá_Quỳnh với bạn_đọc tại Đường sách TP. HCM sáng 18-1 nhằm giới_thiệu quyển sách Nhấn nút tái_tạo - tác_giả Satya_Nadella , CEO của Microsoft - là cuộc chuyện_trò mang nhiều gợi_mở cho cái nhìn về công_nghệ ứng_dụng trong tương_lai . Sách được chú_ý không_chỉ bởi nó được một trong 3 CEO lừng_danh của Microsoft viết ra , tất_nhiên , vai_trò của Satya trong việc định_hướng cho Microsoft để có_thể chuyển_đổi cục_diện của tập_đoàn này khi lần_lượt các đối_thủ đang 
- Reference summary: Một cuốn sách thú_vị về ' hành_trình tìm lại linh_hồn cho Microsoft ' vừa ra_mắt bạn_đọc .
- Predicted summary: Nghệ_thuật và tầm nhìn của ông trong thế_giới công_nghệ được trình_bày như những câu_chuyện gần_gũi , có_thể phù_hợp với " khẩu_vị " nhiều người , miễn_là có quan_tâm đến sự phát_triển của công_nghệ đang làm thay_đổi thế_giới như_thế_nào Tâm_đắc với tác_phẩm , Nguyễn_Bá_Quỳnh - nguyên Giám_đốc khối khách_hàng Chính_phủ và doanh_nghiệp Nhà_nước của Microsoft - cho_rằng nhà_xuất_bản Trẻ ấn_hành quyển sách này thật đúng lúc , nhất_là khi mọi người đang nhắc nhiều đến cuộc cách_mạng công_nghệ 4.0 . 

### Case 2 - guid 15460
- ROUGE-1/2/L: `0.2080` / `0.0855` / `0.1466`
- Article snippet: Xin Thủ_tướng cho_biết thông_điệp của Việt_Nam tại Hội_nghị lần này ? Thủ_tướng Nguyễn_Xuân_Phúc : Trước_hết , chúng_tôi hoan_nghênh nỗ_lực của Thái_Lan , nước Chủ_tịch ASEAN 2019 thúc_đẩy hợp_tác trên tinh_thần Chủ_đề của năm 2019 về " Tăng_cường đối_tác vì sự bền_vững , " hướng đến Cộng_đồng ASEAN phát_triển vững_mạnh trên cả 3 trụ_cột , hướng đến người_dân và lấy người_dân làm trung_tâm . Việt_Nam ủng_hộ và sẽ tích_cực tham_gia triển_khai các sáng_kiến của Thái_Lan , trong đó có tăng_cường ph
- Reference summary: Nhân_dịp tham_dự Hội_nghị cấp cao ASEAN lần thứ 34 tại Bangkok ( Thái_Lan ) trong hai ngày 22-23/6 , Thủ_tướng Chính_phủ Nguyễn_Xuân_Phúc đã trả_lời phỏng_vấn báo The_Nation ( Thái_Lan ) .
- Predicted summary: Nhằm thúc_đẩy quan_hệ hợp_tác theo các hướng như trên , theo tôi trước_mắt hai bên cần tập_trung một_số công_việc cụ_thể như : ( i ) sớm hoàn_tất xây_dựng Chương_trình Hành_động triển_khai quan_hệ Đối_tác Chiến_lược Việt_Nam - Thái_Lan giai_đoạn 2019-2024 ; ( ii ) tăng_cường trao_đổi đoàn , đặc_biệt là đoàn cấp cao ; ( iii ) triển_khai hiệu_quả Bản_Ghi_nhớ về hợp_tác lao_động và Thoả_thuận về Phái_cử và Tiếp_nhận lao_động giữa hai nước ( ký 2015 ) ; ( iv ) phối_hợp chính_sách hợp_tác tiểu_vùng M

### Case 3 - guid 3583
- ROUGE-1/2/L: `0.1481` / `0.0000` / `0.1481`
- Article snippet: Công_an TP Vinh ( Nghệ_An ) cho_biết đã mời bà P. T.N . ( 35 tuổi , ngụ phường Trung_Đô ) để làm rõ vụ_việc bị " tố " hành_hung chị P. T.H . ( 21 tuổi , quê huyện Hưng_Nguyên ) phải nhập_viện điều_trị trong tình_trạng có nguy_cơ sẩy_thai . Chị H. là cô_giáo thực_tập tập tại Trường mầm_non Việt - Lào ( TP Vinh ) . Nhiều người can_ngăn , vẫn đánh Ông Lê_Trường_Sơn , phó trưởng_Phòng GD-ĐT TP Vinh , cho_biết thông_tin ban_đầu , chiều 21-3 , sau khi đón con về nhà bà N. phát_hiện phía chân trái của 
- Reference summary: Chị P. T.H - cô_giáo thực_tập Trường mầm_non Việt - Lào , cho_biết để giữ an_toàn cho thai_nhi , chị phải quỳ xin_lỗi phụ_huynh và học_sinh chứ chị không hề đánh bé .
- Predicted summary: Chị H. Chị H.
