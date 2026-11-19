# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): `X`
- Lớp: `L3B`
- Repo của bàn: `K5-L3B-DAY10-X-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8): `S1`

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; bàn 3 người thì để trống dòng 4. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 |     Phạm Thanh An      |   2A202603913	   |   Kỹ sư cổng  |      Thành viên       |
|   2 |      Cung Đức Anh     |    2A202603814  |  Sản phẩm và kinh doanh   |   Thành viên          |
|   3 |      Đỗ Quốc Khánh     |   2A202603823   |   Kỹ sư cổng  |    Thành viên         |
|   4 |        Mai Lê Bá Vương   |   2A202603872   |  Vận hành và pháp lý   |     Trưởng nhóm        |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## PhamThanhAn-2A202603913

### Phần việc phụ trách

Kỹ sư cổng; phụ trách rà chất lượng và regression, đối chiếu pass rate/pass_k với các ngưỡng đã ký; cập nhật checklist nhóm 1 ở Phiếu C C11.

### Đóng góp cụ thể

Tham gia kiểm tra kết quả sau sửa trên cả bộ nền và S1, bảo đảm các ca đúng không bị hỏng khi xử lý các lỗi của thẻ; đối chiếu các chỉ số an toàn trước khi chốt v2.

### Bằng chứng

Phiếu C C11 nhóm 1; `R-base-after-20261119-185709-dc20f3` (110/110) và `R-S1-grade-20261119-185718-dc20f3` (65/65, wrongful refund/fault/PII đều 0); quyết định v2 tại C12.

### Exit ticket

Học được rằng một guard chỉ được xem là sửa tốt khi vừa chặn lỗi vừa giữ các ca hợp lệ và regression vẫn xanh. Chưa chắc các biến thể câu chữ và hidden test có bao phủ hết cách khách diễn đạt ngoài bộ visible.

## CungDucAnh-2A202603814

### Phần việc phụ trách

Sản phẩm và kinh doanh; phụ trách tiêu chí, bản đồ dữ liệu và theo dõi chi phí/ROI; cập nhật checklist nhóm 2 và 6 tại Phiếu C C11.

### Đóng góp cụ thể

Đối chiếu lời khai của khách với tracking làm nguồn sự thật cho quyết định hoàn; rà ngưỡng kinh doanh đã ký và kết quả cost/ROI sau sửa.

### Bằng chứng

Người ký tiêu chí trong `config/acceptance_criteria.json`; commit ký `bb34c43`; Phiếu B B3 và Phiếu C C3.5/C5, C11 nhóm 2 và 6; `R-S1-after-20261119-185655-dc20f3` (cost `5.171đ/ticket`, ROI `0,93`).

### Exit ticket

Học được rằng tiêu chí cần ký trước khi xem kết quả và trường nguồn sự thật phải được phân biệt với lời khách hoặc bản sao của model. Chưa chắc độ tươi của tracking và cost/ROI sẽ giữ nguyên trên dữ liệu, lưu lượng thật.

## DoQuocKhanh-2A202603823

### Phần việc phụ trách

Kỹ sư cổng; phụ trách quyền hạn, kiểm soát tool ghi và giới hạn strike; cập nhật checklist nhóm 3 và 4 tại Phiếu C C11.

### Đóng góp cụ thể

Rà các cổng trước thao tác ghi, quy tắc lọc trường gửi hãng và giới hạn tối đa 2 strike/hãng/ngày; đối chiếu các ca S1-40–S1-43 để giữ khoản hoàn đúng trong khi chặn strike vượt hạn mức.

### Bằng chứng

Phiếu B B4 và C7; `lab10/guards.py`, `config/operating_gates.json`; Phiếu C C11 nhóm 3 và 4; trace S1-40–S1-43 và `R-S1-grade-20261119-185718-dc20f3`.

### Exit ticket

Học được rằng chặn một lệnh ghi không đồng nghĩa đã dừng toàn bộ luồng; phải chọn deny hay escalate theo hậu quả cần ngăn. Chưa chắc bộ đếm strike của World mô phỏng sẽ khớp ranh giới 24 giờ và dữ liệu vận hành thật.

## MaiLeBaVuong-2A202603872

### Phần việc phụ trách

Trưởng nhóm, vận hành và pháp lý; điều phối các checkpoint, reviewer/runbook, monitor, risk register và quyết định Gate 1 v2.

### Đóng góp cụ thể

Điều phối việc sửa sau thẻ S1, rà tracking completeness và thông báo hãng không chứa dữ liệu khách, cập nhật Runbook 4–5 và chốt quyết định dựa trên grade cùng các ngưỡng đã ký.

### Bằng chứng

Phiếu C C8–C12; `lab10/monitors.py`; `R-S1-after-20261119-185655-dc20f3`, `R-base-after-20261119-185709-dc20f3` và `R-S1-grade-20261119-185718-dc20f3`; commit chốt v1 `c8fc264` và nhận thẻ `5df88bc`.

### Exit ticket

Học được rằng quyết định tiếp tục phải gắn với ngưỡng đã ký, số đo và người chịu trách nhiệm xử lý cảnh báo. Chưa chắc tải reviewer giờ cao điểm và tracking stale nhưng đủ trường sẽ diễn biến thế nào trong pilot thật; cần đo trước Bước đánh giá 2.
