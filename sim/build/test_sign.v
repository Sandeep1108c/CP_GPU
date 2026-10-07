
module test;
    reg signed [17:0] curr_x, curr_y, end_x, end_y;
    reg signed [17:0] dx, dy;
    reg               sx_dir, sy_dir;
    reg signed [18:0] err;

    wire signed [19:0] e2     = err <<< 1;
    wire signed [19:0] neg_dy = -dy;
    wire signed [19:0] pos_dx = dx;

    reg signed [17:0] next_x, next_y;
    reg signed [18:0] next_err, temp_err;

    always @(*) begin
        next_x   = curr_x;
        next_y   = curr_y;
        temp_err = err;

        if (e2 > neg_dy) begin
            temp_err = temp_err - dy;
            next_x   = curr_x + (sx_dir ? 18'sd1 : -18'sd1);
        end

        if (e2 < pos_dx) begin
            temp_err = temp_err + dx;
            next_y   = curr_y + (sy_dir ? 18'sd1 : -18'sd1);
        end

        next_err = temp_err;
    end

    initial begin
        // Steep slope: (10, 10) to (15, 30)
        curr_x = 10; curr_y = 10;
        end_x  = 15; end_y  = 30;
        dx = 5; dy = 20;
        sx_dir = 1; sy_dir = 1;
        err = dx - dy;
        #1;

        while (curr_x != end_x || curr_y != end_y) begin
            $display("Pixel: (%0d, %0d)", curr_x, curr_y);
            #1;
            curr_x = next_x;
            curr_y = next_y;
            err = next_err;
        end
        $display("Done at (%0d, %0d)", curr_x, curr_y);
        $finish;
    end
endmodule
