/** simple script to create a .mdb file for file-test db
 *
 * requires library jackcess (http://jackcess.sourceforge.net/)
 *   and a few more libraries required by jackcess (see 
 *   http://jackcess.sourceforge.net/dependencies.html
 *   and http://search.maven.org/#browse ),
 *   all as jar files within current working dir
 *
 * (Currently, ls *.jar returns:
 *  commons-lang-2.6.jar  commons-logging-1.1.jar  jackcess-2.0.3.jar  
 *  log4j-1.2.9.jar  poi-3.9.jar)
 *
 * Then run 
 * $ javac -cp ".:*" CreateMdb.java
 * $ java -cp ".:*" CreateMdb test.mdb
 *
 * Christian Herdtweck, intra2net, March 2014
 */

import com.healthmarketscience.jackcess.*;
import java.io.File;
import java.io.IOException;

class CreateMdb {
    public static void main(String[] args) throws IOException {
        //for (String arg : args) {
        //    System.out.println(arg);
        //}
        //System.exit(0);

        if (args.length == 0) {
            System.out.println("need file to write to as arg!");
            System.exit(1);
        }

        System.out.println(System.getenv("CLASSPATH"));

        String file_name = args[0];
        System.out.print("Will write to file ");
        System.out.println(file_name);

        File file = new File(file_name);
        Database db = new DatabaseBuilder(file)
            .setFileFormat(Database.FileFormat.V2000)
            .create();

        Table table = new TableBuilder("Test")
            .addColumn(new ColumnBuilder("ID", DataType.LONG)
                     .setAutoNumber(true))
          .addColumn(new ColumnBuilder("Name", DataType.TEXT))
          .addColumn(new ColumnBuilder("Salary", DataType.MONEY))
          .addColumn(new ColumnBuilder("StartDate", DataType.SHORT_DATE_TIME))
          .toTable(db);
        System.out.println("done");
    }
}

