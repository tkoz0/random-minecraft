import java.util.Random;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;

class JavaRandom
{
    public static void main(String[] args) throws IOException, Exception
    {
        String outf = null;
        long calls;
        long seed;
        String func = null;
        Integer param = null;
        if (args.length == 4)
        {
            outf = args[0];
            calls = Long.parseLong(args[1]);
            seed = Long.parseLong(args[2]);
            func = args[3];
        }
        else if (args.length == 5)
        {
            outf = args[0];
            calls = Long.parseLong(args[1]);
            seed = Long.parseLong(args[2]);
            func = args[3];
            param = Integer.parseInt(args[4]);
        }
        else throw new Exception();
        // open output file, use stdout if specified as -
        DataOutputStream dos;
        if (outf.equals("-"))
            dos = new DataOutputStream(System.out);
        else
            dos = new DataOutputStream(new BufferedOutputStream(
                                        new FileOutputStream(outf)));
        Random jrand = new Random(seed);
        // generate random numbers and write as little endian binary data
        if (func.equals("nextBytes"))
        {
            byte[] byte_arr = new byte[param];
            for (long i = 0; i < calls; ++i)
            {
                jrand.nextBytes(byte_arr);
                dos.write(byte_arr,0,byte_arr.length);
            }
        }
        else if (func.equals("nextInt"))
        {
            if (param == null)
            {
                for (long i = 0; i < calls; ++i)
                    dos.writeInt(jrand.nextInt());
            }
            else
            {
                for (long i = 0; i < calls; ++i)
                    dos.writeInt(jrand.nextInt(param));
            }
        }
        else if (func.equals("nextLong"))
        {
            for (long i = 0 ; i < calls; ++i)
                dos.writeLong(jrand.nextLong());
        }
        else if (func.equals("nextBoolean"))
        {
            for (long i = 0; i < calls; ++i)
                dos.writeBoolean(jrand.nextBoolean());
        }
        else if (func.equals("nextFloat"))
        {
            for (long i = 0; i < calls; ++i)
                dos.writeFloat(jrand.nextFloat());
        }
        else if (func.equals("nextDouble"))
        {
            for (long i = 0; i < calls; ++i)
                dos.writeDouble(jrand.nextDouble());
        }
        else if (func.equals("nextGaussian"))
        {
            for (long i = 0; i < calls; ++i)
                dos.writeDouble(jrand.nextGaussian());
        }
        else throw new Exception();
        dos.flush();
        dos.close();
    }
}
