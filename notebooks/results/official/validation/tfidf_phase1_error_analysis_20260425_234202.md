# TF-IDF Short Error Analysis (20260425_234202)

- Selected official `top_k`: `2`
- Sample size: `200`
- Mean ROUGE-1/2/L: `0.4773` / `0.1400` / `0.2701`
- ROUGE-L spread (p10 -> p90): `0.2115` -> `0.3292`
- Mean compression ratio: `0.1162`
- Mean repetition rate: `0.0108`

## Observations
- Worst samples mostly show very low overlap with references despite low repetition, suggesting content-selection misses rather than duplication errors.
- Higher-ROUGE samples tend to have moderate compression, indicating `top_k=2` balances compactness and overlap.
- ROUGE-2 remains lower than ROUGE-1/ROUGE-L, which is expected for an extractive baseline under strict bigram overlap scoring.

## Worst 5 by ROUGE-L
|   guid |   rouge1_f |   rouge2_f |   rougeL_f |   compression_ratio |   repetition_rate |   article_char_len |   reference_char_len |
|-------:|-----------:|-----------:|-----------:|--------------------:|------------------:|-------------------:|---------------------:|
|  10768 |  0         |   0        |  0         |          0.0075692  |                 0 |               4624 |                  131 |
|    788 |  0.0952381 |   0        |  0.0952381 |          0.013941   |                 0 |               1865 |                  122 |
|  16686 |  0.208955  |   0        |  0.119403  |          0.0228916  |                 0 |               2490 |                  165 |
|  18313 |  0.148148  |   0        |  0.123457  |          0.00974729 |                 0 |               2770 |                  217 |
|  16537 |  0.175     |   0.025641 |  0.125     |          0.00618865 |                 0 |               4686 |                  219 |

## Failure Cases (3 lowest ROUGE-L)
### Case 1 - guid 10768
- ROUGE-1/2/L: `0.0000` / `0.0000` / `0.0000`
- Article snippet: Máy_bay Ấn_Độ bị bắn hạ ngày 27/2 . Căng_thẳng ở biên_giới giữa Ấn_Độ và Pakistan tuần này đã đẩy hai đối_thủ sở_hữu hạt_nhân ở Nam_Á đến gần bờ vực xung_đột hơn bất_cứ lúc_nào trong hai thập_niên . Ấn_Độ và Pakistan là hai quốc_gia láng_giềng luôn trong tình_trạng căng_thẳng do yếu_tố lịch_sử . Anh rút khỏi thuộc_địa Ấn_Độ vào năm 1947 , dẫn đến việc nơi này chia tách thành hai quốc_gia : Ấn_Độ - nơi đa_số người theo đạo Hindu sinh_sống và Pakistan - nơi đa_số người Hồi_giáo sinh_sống . Ấn_Độ ,
- Reference summary: Ấn_Độ và Pakistan bắn hạ máy_bay của nhau khiến căng_thẳng sôi_sục nhưng tình_hình được xoa_dịu nhờ vụ phóng_thích phi_công Ấn_Độ .
- Predicted summary: Đồ_hoạ : CNN . Video : Next_Media .

### Case 2 - guid 788
- ROUGE-1/2/L: `0.0952` / `0.0000` / `0.0952`
- Article snippet: Chiều 29/7 , Đại_tá Trần_Mưu , Phó Giám_đốc Công_an TP Đà_Nẵng xác_nhận đã có quyết_định tống_đạt quyết_định khởi_tố vụ án , khởi_tố bị_can , bắt tạm giam trở_lại đối_với Bùi_Văn_Hời ( 34 tuổi , ngụ huyện Hưng_Hà , tỉnh Thái_Bình ) về tội giết người . Hiện , tất_cả các quyết_định này đã được VKS cùng cấp phê_chuẩn . Trước_đây , Hời từng bị bắt_giữ vì là nghi phạm sát_hại con_gái rồi phi_tang xác xuống sông Hàn . Trong quá_trình điều_tra , Hời khai nhận hành_vi của mình . Tuy_nhiên , sau đó , hết
- Reference summary: Quyết_định bắt_giữ Hời đã được VKSND TP Đà_Nẵng phê_duyệt . Như_vậy , sau thời_gian được thả , Hời đã bị bắt_giữ trở_lại .
- Predicted summary: nảy_sinh mâu_thuẫn . HCM .

### Case 3 - guid 16686
- ROUGE-1/2/L: `0.2090` / `0.0000` / `0.1194`
- Article snippet: Thanh_tra Chính_phủ giải_trình về việc mở_rộng phạm_vi điều_chỉnh này : " Dự_thảo đã quy_định việc áp_dụng luật Phòng_chống tham_nhũng đối_với tổ_chức xã_hội , doanh_nghiệp , tổ_chức kinh_tế , trong đó quy_định áp_dụng bắt_buộc một_số chế_định của luật đối_với một_số loại_hình tổ_chức xã_hội , doanh_nghiệp " . " Quy_định này thể_hiện tinh_thần từng bước mở_rộng phạm_vi điều_chỉnh của luật đối_với khu_vực ngoài nhà_nước " , Thanh_tra Chính_phủ nhận_định . Bước_đầu , đa_số ý_kiến trong nhóm nghiên
- Reference summary: Đó là một trong những điểm mới đáng chú_ý của dự_án luật Phòng_chống tham_nhũng ( sửa_đổi ) vừa được Thanh_tra Chính_phủ trình Uỷ_ban Tư_pháp của Quốc_hội thẩm_tra .
- Predicted summary: HCM ) , bị tuyên_án chung_thân năm 2010 - Ảnh : T.T . D .

## Best 5 by ROUGE-L
|   guid |   rouge1_f |   rouge2_f |   rougeL_f |   compression_ratio |   repetition_rate |   article_char_len |   reference_char_len |
|-------:|-----------:|-----------:|-----------:|--------------------:|------------------:|-------------------:|---------------------:|
|   3001 |   0.830409 |   0.721893 |   0.783626 |           0.11934   |         0.0232558 |               2120 |                  232 |
|  14583 |   0.650407 |   0.644628 |   0.650407 |           0.0297731 |         0         |               4803 |                  246 |
|   2597 |   0.644444 |   0.409091 |   0.533333 |           0.0460952 |         0         |               2625 |                  156 |
|   9242 |   0.560748 |   0.380952 |   0.46729  |           0.123699  |         0         |               1633 |                  135 |
|   7340 |   0.595506 |   0.306818 |   0.449438 |           0.249097  |         0         |               1385 |                  210 |
