import ezdxf
from ezdxf import units
from ezdxf.math import Vec2
from ezdxf.render import mleader
import math

beam_type = request.form['type']
print(beam_type)
if beam_type == "Cantilever":
        beam_length = float(request.form['beam_length'])
        clear_span = beam_length
        exposure = request.form['exposure']
        cd = 750
        wall_thickness = float(request.form['wall_thickness'])
        span_d = 4
        fck = int(request.form['fck'])
        fy = int(request.form['fy'])
        # ------------------step-1-------------geometery
        effective_length = clear_span + cd / 2000

        def get_nominal_cover(exposure_condition):
            covers = {
                "Mild": 20,
                "Moderate": 30,
                "Severe": 45,
                "Very severe": 50,
                "Extreme": 75
            }
            return covers.get(exposure_condition, "Exposure not found")

        md = 32
        bt = 8
        nominal_cover = get_nominal_cover(exposure)
        ed = effective_length * 1000 / span_d
        ed1 = effective_length * 1000 / span_d + bt + md / 2 + nominal_cover
        provided_depth = math.ceil(ed1 / 25) * 25
        print("provide Overall depth", provided_depth, "mm")
        effective_depth = provided_depth - nominal_cover - md / 2 - bt
        print("revised Effective depth", effective_depth, "mm")
        revised_effective_length = clear_span * 1000 + effective_depth / 2
        print("revised Effective Length: ", revised_effective_length, "mm")
        # -----------------------Step-2---------------------------------------------
        self_weight = provided_depth * wall_thickness * 25 / (10 ** 6)

        def get_point_loads():
            point_loads = []
            num_point_loads = 0
            for i in range(1, num_point_loads + 1):
                magnitude = float(request.form[f'magnitude_{i}'])
                position = float(request.form[f'position_{i}'])
                point_loads.append((magnitude, position))

            return f"Point loads: {point_loads}"

        def get_tcmax(concrete_grade):
            # Dictionary containing the tcmax values for different concrete grades
            tcmax_values = {
                15: 2.5,
                20: 2.8,
                25: 3.1,
                30: 3.5,
                35: 3.7,
                40: 4.0
            }

            # Return the tcmax value for the given concrete grade
            return tcmax_values.get(concrete_grade, "Grade not found")

        # this would be user input in practice
        tcmax = get_tcmax(fck)

        def calculate_sf_bm(point_loads, udl, beam_length):
            x = np.linspace(0, beam_length, 500)
            sf = np.zeros_like(x)
            bm = np.zeros_like(x)

            # Add effects of UDL
            udl_mag, udl_start, udl_end = udl, 0, revised_effective_length
            for i, xi in enumerate(x):
                if xi >= udl_start and xi <= udl_end:
                    sf[i] -= udl_mag * (xi - udl_start)
                    bm[i] -= udl_mag * (xi - udl_start) ** 2 / 2

            # Add effects of point loads
            for magnitude, position in point_loads:
                for i, xi in enumerate(x):
                    if xi >= position:
                        sf[i] -= magnitude
                        bm[i] -= magnitude * (xi - position)

            # Find the maximum absolute SF and the maximum BM (ignoring the sign for SF)
            max_sf = np.max(np.abs(sf))
            max_sf_value = max(sf[np.argmax(np.abs(sf))], sf[np.argmin(sf)],
                               key=abs)  # This ensures we get the value with its original sign
            max_bm = np.max(np.abs(bm))
            max_bm_value = max(bm[np.argmax(bm)], bm[np.argmin(bm)],
                               key=abs)  # This ensures we get the value with its original sign

            return x, sf, bm, max_sf_value, max_bm_value

        def plot_sf_bm(x, sf, bm, max_sf_value, max_bm_value):
            fig, axs = plt.subplots(2, 1, figsize=(10, 8))

            # Shear Force plot
            axs[0].plot(x, sf, label="Shear Force", color='blue')
            axs[0].set_ylabel('Shear Force (N)')
            axs[0].grid(True)
            max_sf_x = x[np.argmax(np.abs(sf))]  # Position of max SF
            axs[0].annotate(f'Max SF: {max_sf_value} N', xy=(max_sf_x, max_sf_value),
                            xytext=(max_sf_x, max_sf_value * 1.1),
                            arrowprops=dict(facecolor='black', shrink=0.05))
            axs[0].legend()

            # Bending Moment plot
            axs[1].plot(x, bm, label="Bending Moment", color='red')
            axs[1].set_ylabel('Bending Moment (N.m)')
            axs[1].set_xlabel('Position along beam (m)')
            axs[1].grid(True)
            max_bm_x = x[np.argmax(np.abs(bm))]  # Position of max BM
            axs[1].annotate(f'Max BM: {max_bm_value} N.m', xy=(max_bm_x, max_bm_value),
                            xytext=(max_bm_x, max_bm_value * 1.1),
                            arrowprops=dict(facecolor='black', shrink=0.05))
            axs[1].legend()

            #plt.tight_layout()
            #plt.show()

        # Interactive execution is needed to uncomment and use the following lines:
        point_loads = []
        udl = int(request.form['udl'])
        beam_length = revised_effective_length / 1000
        x, sf, bm, max_sf, max_bm = calculate_sf_bm(point_loads, udl, beam_length)
        #plot_sf_bm(x, sf, bm, max_sf, max_bm)
        ubm = max_bm * 1.5 * -1
        usf = 1.5 * max_sf * -1
        print("ultimate bending moment: ", ubm, "kNm")
        print("ultimate Shear force: ", usf, "kN")
        # -------------------step-3-------------------------------------------
        if (fy == 415):
            mul = .138 * fck * wall_thickness * effective_depth * effective_depth / 1000000
        elif (fy == 250):
            mul = .148 * fck * wall_thickness * effective_depth * effective_depth / 1000000
        elif (fy == 500):
            mul = .133 * fck * wall_thickness * effective_depth * effective_depth / 1000000
        print("Mulimt : ", mul, "kNm")
        if (mul > ubm):
            ultimate_bending_moment = ubm
            b = wall_thickness
            print("The section is Singly Reinforced")
            # ---------------Ast--------------------------------------
            ast = 0.00574712643678161 * (
                    87 * b * effective_depth * fck -
                    9.32737905308882 * (b * fck * (
                    -400 * ultimate_bending_moment * 1000000 + 87 * b * effective_depth ** 2 * fck)) ** 0.5) / fy
            print("ast", ast)
            astmin = 0.85 * b * effective_depth / fy
            print("astmin", astmin)
            astmax = .04 * b * provided_depth
            print("Maximum Ast:", astmax)
            if (astmax < astmin or astmax < ast):
                print("Revise Section,Tensile Reinforcement Exceeds 4% #1")

            # --------------------------------------Top bars------------------------
            if (ast > astmin):
                print("Ast will be governing for steel arrangement")
                main_bar = [12, 16, 20, 25, 32, 40]
                results = []
                for num in main_bar:
                    # Calculate the result
                    result = max(ast / (num * num * .785), 2)
                    results.append((num, math.ceil(result)))

                # Find suitable bar and count
                suitable_bars = [(num, count) for num, count in results if 2 <= count < 5]
                if suitable_bars:
                    main_bar, no_of_bars_top = suitable_bars[0]  # Select the first suitable option
                else:
                    main_bar, no_of_bars_top = (0, 0)  # Default to zero if no suitable option is found

                # Calculate the area of steel provided and percentage
                ab = no_of_bars_top * 0.78539816339744830961566084581988 * main_bar ** 2
                pt = 100 * ab / (b * effective_depth)

                # print(main_bar, no_of_bars, pt)
                main_bar_provided = main_bar
                # no_of_bars = round(ast / (0.78539816339744830961566084581988 * main_bar ** 2), 0)
                print("provide", no_of_bars_top, "-Φ", main_bar, " mm as main bars at the top")
                # ab = no_of_bars * 0.78539816339744830961566084581988 * main_bar ** 2
                # pt = 100 * ab / (b * effective_depth)
                print("percentage of steel provided(Tension Reinforcement): ", pt)
            else:
                main_bar = [12, 16, 20, 25, 32, 40]
                results = []
                for num in main_bar:
                    # Calculate the result
                    result = max(astmin / (num * num * .785), 2)
                    results.append((num, math.ceil(result)))

                # Find suitable bar and count
                suitable_bars = [(num, count) for num, count in results if 2 <= count < 5]
                if suitable_bars:
                    main_bar, no_of_bars_top = suitable_bars[0]  # Select the first suitable option
                else:
                    main_bar, no_of_bars_top = (0, 0)  # Default to zero if no suitable option is found

                # Calculate the area of steel provided and percentage
                ab = no_of_bars_top * 0.78539816339744830961566084581988 * main_bar ** 2
                pt = 100 * ab / (b * effective_depth)

                # print(main_bar, no_of_bars, pt)
                main_bar_provided = main_bar
                # no_of_bars = round(ast / (0.78539816339744830961566084581988 * main_bar ** 2), 0)
                print("provide", no_of_bars_top, "-Φ", main_bar, " mm as main bars at the top")
                # ab = no_of_bars * 0.78539816339744830961566084581988 * main_bar ** 2
                # pt = 100 * ab / (b * effective_depth)
                print("percentage of steel provided(Tension Reinforcement): ", pt)
            # -----------------------------------bottom bars---------------------------------------
            bottom_bar = [12, 16, 20, 25, 32, 40]
            results1 = []
            for num in bottom_bar:
                # Calculate the result
                result1 = max(astmin / (num * num * .785), 2)
                results1.append((num, math.ceil(result1)))

            # Find suitable bar and count
            suitable_bars = [(num, count) for num, count in results1 if 2 <= count < 5]
            if suitable_bars:
                bottom_bar, no_of_bars_bottom = suitable_bars[0]  # Select the first suitable option
            else:
                bottom_bar, no_of_bars_bottom = (0, 0)  # Default to zero if no suitable option is found
            if (no_of_bars_bottom == 0):
                no_of_bars_bottom = 2
                bottom_bar = 12

            # Calculate the area of steel provided and percentage
            ab = no_of_bars_bottom * 0.78539816339744830961566084581988 * bottom_bar ** 2
            pt = 100 * ab / (b * effective_depth)

            # print(main_bar, no_of_bars, pt)
            bottom_bar_provided = bottom_bar
            # no_of_bars = round(ast / (0.78539816339744830961566084581988 * main_bar ** 2), 0)
            print("provide", no_of_bars_bottom, "-Φ", bottom_bar, " mm as main bars at the bottom")

            print("percentage of steel provided(Compression Reinforcement): ", pt)
            # --------------------------check for shear-----------------------------
            ultimate_shear_force = usf
            vu = ultimate_shear_force * 1000
            tv = vu / (b * effective_depth)
            print(effective_depth)
            p = 100 * ast / (b * effective_depth)
            # print(p)

            beta = 0.8 * fck / (6.89 * p)
            f = (0.8 * fck) ** 0.5
            brta = ((1 + 5 * beta) ** 0.5) - 1
            tc = 0.85 * f * brta / (6 * beta)
            # tc=(0.85*((0.8*fck)**0.5)*((1+5*beta)**0.5)-1)/(6*beta)
            print("tc value: ", tc)
            print("tv value: ", tv)
            if (tv > tc and tv <= tcmax):
                Vus = ultimate_shear_force * 1000 - (tc * b * effective_depth)
                print("Vus value: ", Vus)
                stdia = 8
                leg = 2

                sv = 0.87 * fy * effective_depth * leg * 0.78539816339744830961566084581988 * stdia ** 2 / Vus
                print(sv)
                spacing = min(0.75 * effective_depth, 300)
                max_spacing = (spacing // 25) * 25
                # print(max_spacing)
                print("Provide Φ", stdia, "- mm ", leg, "vertical stirrups @", max_spacing, "c/c")
            elif (tv <= tc):
                stdia = 8
                leg = 2

                sv = 0.87 * fy * leg * 0.78539816339744830961566084581988 * stdia ** 2 / (0.4 * wall_thickness)
                spacing = min(0.75 * effective_depth, 300)
                max_spacing = (spacing // 25) * 25
                # print(max_spacing)
                print("Provide Φ", stdia, "- mm ", leg, "vertical stirrups @", max_spacing, "c/c")
            else:
                print("revise section (per Cl. 40.2.3, IS 456: 2000, pp. 72 #2")

            # step 6:Check for Deflection
            l = revised_effective_length
            Actualspan = l / effective_depth
            bd = b * effective_depth / (100 * ast)
            fs = 0.58 * fy * ast / (no_of_bars_top * 0.78539816339744830961566084581988 * main_bar ** 2)

            mf = 1 / (0.225 + 0.003228 * fs - 0.625 * math.log10(bd))
            allowablespan = 7 * mf
            print("modification factor: ", mf)
            # -----------development length-------------
            phi = main_bar
            print(main_bar)
            print(bottom_bar)
            tss = 0.87 * fy
            if (fck == 20):
                tbd = 1.2 * 1.6
            elif (fck == 25):
                tbd = 1.4 * 2.24
            elif (fck == 30):
                tbd = 1.5 * 2.4
            elif (fck == 35):
                tbd = 1.7 * 2.72
            elif (fck >= 40):
                tbd = 1.9 * 3.04
            ld = phi * tss / (4 * tbd)
            print(ld)
            # ---------------shear reinforcement--------------------
            as1 = 0.1 * wall_thickness * effective_depth / 100
            no_of_bars_shear_face = math.ceil((as1 / 2) / (0.785 * 144))
            spacing_of_bars = provided_depth - nominal_cover * 2 - stdia * 2 - main_bar / 2 - bottom_bar_provided / 2
            no_of_bars_shear = math.ceil((spacing_of_bars / wall_thickness) - 1)
            print(no_of_bars_shear)
            if (allowablespan > Actualspan):
                print(" The section is safe under deflection")
            else:
                print(" revise section #3")


