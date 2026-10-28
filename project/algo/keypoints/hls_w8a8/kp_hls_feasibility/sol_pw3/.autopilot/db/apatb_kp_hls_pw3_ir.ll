; ModuleID = 'F:/PLD_new/Sign-Language-Vision-Recognition/project/algo/keypoints/hls_w8a8/kp_hls_feasibility/sol_pw3/.autopilot/db/a.g.ld.5.gdce.bc'
source_filename = "llvm-link"
target datalayout = "e-m:e-i64:64-i128:128-i256:256-i512:512-i1024:1024-i2048:2048-i4096:4096-n8:16:32:64-S128-v16:16-v24:32-v32:32-v48:64-v96:128-v192:256-v256:256-v512:512-v1024:1024"
target triple = "fpga64-xilinx-none"

; Function Attrs: noinline
define void @apatb_kp_hls_pw3_ir(i8* noalias nocapture nonnull readonly "maxi" %in, i8* noalias nocapture nonnull readonly "maxi" %w, i64* noalias nocapture nonnull readonly "maxi" %bias, i32* noalias nocapture nonnull readonly "maxi" %M, i32 %F, i8* noalias nocapture nonnull "maxi" %out) local_unnamed_addr #0 {
entry:
  %in_copy = alloca [3456 x i8], align 512
  %w_copy = alloca [3072 x i8], align 512
  %bias_copy = alloca [64 x i64], align 512
  %M_copy = alloca [64 x i32], align 512
  %malloccall = tail call i8* @malloc(i64 4608)
  %out_copy = bitcast i8* %malloccall to [4608 x i8]*
  %0 = bitcast i8* %in to [3456 x i8]*
  %1 = bitcast i8* %w to [3072 x i8]*
  %2 = bitcast i64* %bias to [64 x i64]*
  %3 = bitcast i32* %M to [64 x i32]*
  %4 = bitcast i8* %out to [4608 x i8]*
  call fastcc void @copy_in([3456 x i8]* nonnull %0, [3456 x i8]* nonnull align 512 %in_copy, [3072 x i8]* nonnull %1, [3072 x i8]* nonnull align 512 %w_copy, [64 x i64]* nonnull %2, [64 x i64]* nonnull align 512 %bias_copy, [64 x i32]* nonnull %3, [64 x i32]* nonnull align 512 %M_copy, [4608 x i8]* nonnull %4, [4608 x i8]* %out_copy)
  call void @apatb_kp_hls_pw3_hw([3456 x i8]* %in_copy, [3072 x i8]* %w_copy, [64 x i64]* %bias_copy, [64 x i32]* %M_copy, i32 %F, [4608 x i8]* %out_copy)
  call void @copy_back([3456 x i8]* %0, [3456 x i8]* %in_copy, [3072 x i8]* %1, [3072 x i8]* %w_copy, [64 x i64]* %2, [64 x i64]* %bias_copy, [64 x i32]* %3, [64 x i32]* %M_copy, [4608 x i8]* %4, [4608 x i8]* %out_copy)
  tail call void @free(i8* %malloccall)
  ret void
}

declare noalias i8* @malloc(i64) local_unnamed_addr

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @copy_in([3456 x i8]* noalias readonly, [3456 x i8]* noalias align 512, [3072 x i8]* noalias readonly, [3072 x i8]* noalias align 512, [64 x i64]* noalias readonly, [64 x i64]* noalias align 512, [64 x i32]* noalias readonly, [64 x i32]* noalias align 512, [4608 x i8]* noalias readonly, [4608 x i8]* noalias) unnamed_addr #1 {
entry:
  call fastcc void @onebyonecpy_hls.p0a3456i8([3456 x i8]* align 512 %1, [3456 x i8]* %0)
  call fastcc void @onebyonecpy_hls.p0a3072i8([3072 x i8]* align 512 %3, [3072 x i8]* %2)
  call fastcc void @onebyonecpy_hls.p0a64i64([64 x i64]* align 512 %5, [64 x i64]* %4)
  call fastcc void @onebyonecpy_hls.p0a64i32([64 x i32]* align 512 %7, [64 x i32]* %6)
  call fastcc void @onebyonecpy_hls.p0a4608i8([4608 x i8]* %9, [4608 x i8]* %8)
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @onebyonecpy_hls.p0a3456i8([3456 x i8]* noalias align 512 %dst, [3456 x i8]* noalias readonly %src) unnamed_addr #2 {
entry:
  %0 = icmp eq [3456 x i8]* %dst, null
  %1 = icmp eq [3456 x i8]* %src, null
  %2 = or i1 %0, %1
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  call void @arraycpy_hls.p0a3456i8([3456 x i8]* nonnull %dst, [3456 x i8]* nonnull %src, i64 3456)
  br label %ret

ret:                                              ; preds = %copy, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define void @arraycpy_hls.p0a3456i8([3456 x i8]* %dst, [3456 x i8]* readonly %src, i64 %num) local_unnamed_addr #3 {
entry:
  %0 = icmp eq [3456 x i8]* %src, null
  %1 = icmp eq [3456 x i8]* %dst, null
  %2 = or i1 %1, %0
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  %for.loop.cond1 = icmp sgt i64 %num, 0
  br i1 %for.loop.cond1, label %for.loop.lr.ph, label %copy.split

for.loop.lr.ph:                                   ; preds = %copy
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %for.loop.lr.ph
  %for.loop.idx2 = phi i64 [ 0, %for.loop.lr.ph ], [ %for.loop.idx.next, %for.loop ]
  %dst.addr = getelementptr [3456 x i8], [3456 x i8]* %dst, i64 0, i64 %for.loop.idx2
  %src.addr = getelementptr [3456 x i8], [3456 x i8]* %src, i64 0, i64 %for.loop.idx2
  %3 = load i8, i8* %src.addr, align 1
  store i8 %3, i8* %dst.addr, align 1
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx2, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, %num
  br i1 %exitcond, label %for.loop, label %copy.split

copy.split:                                       ; preds = %for.loop, %copy
  br label %ret

ret:                                              ; preds = %copy.split, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @onebyonecpy_hls.p0a3072i8([3072 x i8]* noalias align 512 %dst, [3072 x i8]* noalias readonly %src) unnamed_addr #2 {
entry:
  %0 = icmp eq [3072 x i8]* %dst, null
  %1 = icmp eq [3072 x i8]* %src, null
  %2 = or i1 %0, %1
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  call void @arraycpy_hls.p0a3072i8([3072 x i8]* nonnull %dst, [3072 x i8]* nonnull %src, i64 3072)
  br label %ret

ret:                                              ; preds = %copy, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define void @arraycpy_hls.p0a3072i8([3072 x i8]* %dst, [3072 x i8]* readonly %src, i64 %num) local_unnamed_addr #3 {
entry:
  %0 = icmp eq [3072 x i8]* %src, null
  %1 = icmp eq [3072 x i8]* %dst, null
  %2 = or i1 %1, %0
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  %for.loop.cond1 = icmp sgt i64 %num, 0
  br i1 %for.loop.cond1, label %for.loop.lr.ph, label %copy.split

for.loop.lr.ph:                                   ; preds = %copy
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %for.loop.lr.ph
  %for.loop.idx2 = phi i64 [ 0, %for.loop.lr.ph ], [ %for.loop.idx.next, %for.loop ]
  %dst.addr = getelementptr [3072 x i8], [3072 x i8]* %dst, i64 0, i64 %for.loop.idx2
  %src.addr = getelementptr [3072 x i8], [3072 x i8]* %src, i64 0, i64 %for.loop.idx2
  %3 = load i8, i8* %src.addr, align 1
  store i8 %3, i8* %dst.addr, align 1
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx2, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, %num
  br i1 %exitcond, label %for.loop, label %copy.split

copy.split:                                       ; preds = %for.loop, %copy
  br label %ret

ret:                                              ; preds = %copy.split, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @onebyonecpy_hls.p0a64i64([64 x i64]* noalias align 512 %dst, [64 x i64]* noalias readonly %src) unnamed_addr #2 {
entry:
  %0 = icmp eq [64 x i64]* %dst, null
  %1 = icmp eq [64 x i64]* %src, null
  %2 = or i1 %0, %1
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  call void @arraycpy_hls.p0a64i64([64 x i64]* nonnull %dst, [64 x i64]* nonnull %src, i64 64)
  br label %ret

ret:                                              ; preds = %copy, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define void @arraycpy_hls.p0a64i64([64 x i64]* %dst, [64 x i64]* readonly %src, i64 %num) local_unnamed_addr #3 {
entry:
  %0 = icmp eq [64 x i64]* %src, null
  %1 = icmp eq [64 x i64]* %dst, null
  %2 = or i1 %1, %0
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  %for.loop.cond1 = icmp sgt i64 %num, 0
  br i1 %for.loop.cond1, label %for.loop.lr.ph, label %copy.split

for.loop.lr.ph:                                   ; preds = %copy
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %for.loop.lr.ph
  %for.loop.idx2 = phi i64 [ 0, %for.loop.lr.ph ], [ %for.loop.idx.next, %for.loop ]
  %dst.addr = getelementptr [64 x i64], [64 x i64]* %dst, i64 0, i64 %for.loop.idx2
  %src.addr = getelementptr [64 x i64], [64 x i64]* %src, i64 0, i64 %for.loop.idx2
  %3 = load i64, i64* %src.addr, align 8
  store i64 %3, i64* %dst.addr, align 8
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx2, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, %num
  br i1 %exitcond, label %for.loop, label %copy.split

copy.split:                                       ; preds = %for.loop, %copy
  br label %ret

ret:                                              ; preds = %copy.split, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @onebyonecpy_hls.p0a64i32([64 x i32]* noalias align 512 %dst, [64 x i32]* noalias readonly %src) unnamed_addr #2 {
entry:
  %0 = icmp eq [64 x i32]* %dst, null
  %1 = icmp eq [64 x i32]* %src, null
  %2 = or i1 %0, %1
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  call void @arraycpy_hls.p0a64i32([64 x i32]* nonnull %dst, [64 x i32]* nonnull %src, i64 64)
  br label %ret

ret:                                              ; preds = %copy, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define void @arraycpy_hls.p0a64i32([64 x i32]* %dst, [64 x i32]* readonly %src, i64 %num) local_unnamed_addr #3 {
entry:
  %0 = icmp eq [64 x i32]* %src, null
  %1 = icmp eq [64 x i32]* %dst, null
  %2 = or i1 %1, %0
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  %for.loop.cond1 = icmp sgt i64 %num, 0
  br i1 %for.loop.cond1, label %for.loop.lr.ph, label %copy.split

for.loop.lr.ph:                                   ; preds = %copy
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %for.loop.lr.ph
  %for.loop.idx2 = phi i64 [ 0, %for.loop.lr.ph ], [ %for.loop.idx.next, %for.loop ]
  %dst.addr = getelementptr [64 x i32], [64 x i32]* %dst, i64 0, i64 %for.loop.idx2
  %src.addr = getelementptr [64 x i32], [64 x i32]* %src, i64 0, i64 %for.loop.idx2
  %3 = load i32, i32* %src.addr, align 4
  store i32 %3, i32* %dst.addr, align 4
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx2, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, %num
  br i1 %exitcond, label %for.loop, label %copy.split

copy.split:                                       ; preds = %for.loop, %copy
  br label %ret

ret:                                              ; preds = %copy.split, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @onebyonecpy_hls.p0a4608i8([4608 x i8]* noalias %dst, [4608 x i8]* noalias readonly %src) unnamed_addr #2 {
entry:
  %0 = icmp eq [4608 x i8]* %dst, null
  %1 = icmp eq [4608 x i8]* %src, null
  %2 = or i1 %0, %1
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  call void @arraycpy_hls.p0a4608i8([4608 x i8]* nonnull %dst, [4608 x i8]* nonnull %src, i64 4608)
  br label %ret

ret:                                              ; preds = %copy, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define void @arraycpy_hls.p0a4608i8([4608 x i8]* %dst, [4608 x i8]* readonly %src, i64 %num) local_unnamed_addr #3 {
entry:
  %0 = icmp eq [4608 x i8]* %src, null
  %1 = icmp eq [4608 x i8]* %dst, null
  %2 = or i1 %1, %0
  br i1 %2, label %ret, label %copy

copy:                                             ; preds = %entry
  %for.loop.cond1 = icmp sgt i64 %num, 0
  br i1 %for.loop.cond1, label %for.loop.lr.ph, label %copy.split

for.loop.lr.ph:                                   ; preds = %copy
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %for.loop.lr.ph
  %for.loop.idx2 = phi i64 [ 0, %for.loop.lr.ph ], [ %for.loop.idx.next, %for.loop ]
  %dst.addr = getelementptr [4608 x i8], [4608 x i8]* %dst, i64 0, i64 %for.loop.idx2
  %src.addr = getelementptr [4608 x i8], [4608 x i8]* %src, i64 0, i64 %for.loop.idx2
  %3 = load i8, i8* %src.addr, align 1
  store i8 %3, i8* %dst.addr, align 1
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx2, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, %num
  br i1 %exitcond, label %for.loop, label %copy.split

copy.split:                                       ; preds = %for.loop, %copy
  br label %ret

ret:                                              ; preds = %copy.split, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @copy_out([3456 x i8]* noalias, [3456 x i8]* noalias readonly align 512, [3072 x i8]* noalias, [3072 x i8]* noalias readonly align 512, [64 x i64]* noalias, [64 x i64]* noalias readonly align 512, [64 x i32]* noalias, [64 x i32]* noalias readonly align 512, [4608 x i8]* noalias, [4608 x i8]* noalias readonly) unnamed_addr #4 {
entry:
  call fastcc void @onebyonecpy_hls.p0a3456i8([3456 x i8]* %0, [3456 x i8]* align 512 %1)
  call fastcc void @onebyonecpy_hls.p0a3072i8([3072 x i8]* %2, [3072 x i8]* align 512 %3)
  call fastcc void @onebyonecpy_hls.p0a64i64([64 x i64]* %4, [64 x i64]* align 512 %5)
  call fastcc void @onebyonecpy_hls.p0a64i32([64 x i32]* %6, [64 x i32]* align 512 %7)
  call fastcc void @onebyonecpy_hls.p0a4608i8([4608 x i8]* %8, [4608 x i8]* %9)
  ret void
}

declare void @free(i8*) local_unnamed_addr

declare void @apatb_kp_hls_pw3_hw([3456 x i8]*, [3072 x i8]*, [64 x i64]*, [64 x i32]*, i32, [4608 x i8]*)

; Function Attrs: argmemonly noinline norecurse willreturn
define internal fastcc void @copy_back([3456 x i8]* noalias, [3456 x i8]* noalias readonly align 512, [3072 x i8]* noalias, [3072 x i8]* noalias readonly align 512, [64 x i64]* noalias, [64 x i64]* noalias readonly align 512, [64 x i32]* noalias, [64 x i32]* noalias readonly align 512, [4608 x i8]* noalias, [4608 x i8]* noalias readonly) unnamed_addr #4 {
entry:
  call fastcc void @onebyonecpy_hls.p0a4608i8([4608 x i8]* %8, [4608 x i8]* %9)
  ret void
}

define void @kp_hls_pw3_hw_stub_wrapper([3456 x i8]*, [3072 x i8]*, [64 x i64]*, [64 x i32]*, i32, [4608 x i8]*) #5 {
entry:
  call void @copy_out([3456 x i8]* null, [3456 x i8]* %0, [3072 x i8]* null, [3072 x i8]* %1, [64 x i64]* null, [64 x i64]* %2, [64 x i32]* null, [64 x i32]* %3, [4608 x i8]* null, [4608 x i8]* %5)
  %6 = bitcast [3456 x i8]* %0 to i8*
  %7 = bitcast [3072 x i8]* %1 to i8*
  %8 = bitcast [64 x i64]* %2 to i64*
  %9 = bitcast [64 x i32]* %3 to i32*
  %10 = bitcast [4608 x i8]* %5 to i8*
  call void @kp_hls_pw3_hw_stub(i8* %6, i8* %7, i64* %8, i32* %9, i32 %4, i8* %10)
  call void @copy_in([3456 x i8]* null, [3456 x i8]* %0, [3072 x i8]* null, [3072 x i8]* %1, [64 x i64]* null, [64 x i64]* %2, [64 x i32]* null, [64 x i32]* %3, [4608 x i8]* null, [4608 x i8]* %5)
  ret void
}

declare void @kp_hls_pw3_hw_stub(i8* noalias nocapture nonnull readonly, i8* noalias nocapture nonnull readonly, i64* noalias nocapture nonnull readonly, i32* noalias nocapture nonnull readonly, i32, i8* noalias nocapture nonnull)

attributes #0 = { noinline "fpga.wrapper.func"="wrapper" }
attributes #1 = { argmemonly noinline norecurse willreturn "fpga.wrapper.func"="copyin" }
attributes #2 = { argmemonly noinline norecurse willreturn "fpga.wrapper.func"="onebyonecpy_hls" }
attributes #3 = { argmemonly noinline norecurse willreturn "fpga.wrapper.func"="arraycpy_hls" }
attributes #4 = { argmemonly noinline norecurse willreturn "fpga.wrapper.func"="copyout" }
attributes #5 = { "fpga.wrapper.func"="stub" }

!llvm.dbg.cu = !{}
!llvm.ident = !{!0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0}
!llvm.module.flags = !{!1, !2, !3}
!blackbox_cfg = !{!4}

!0 = !{!"clang version 7.0.0 "}
!1 = !{i32 2, !"Dwarf Version", i32 4}
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 1, !"wchar_size", i32 4}
!4 = !{}
