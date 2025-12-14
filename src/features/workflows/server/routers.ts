// F:\nodebase_final_pro\src\server\api\routers\workflows.ts
import "server-only";
import { generateSlug } from "random-word-slugs";
import prisma from "@/lib/db";
import {
  createTRPCRouter,
  premiumProcedure, // ✅ Sirf Paid users k liye
  protectedProcedure, // ✅ Normal logged in users k liye
} from "@/trpc/init";
import { TRPCError } from "@trpc/server";
import z from "zod";
import { PAGINATION } from "@/config/constants";

export const workflowsRouter = createTRPCRouter({
  // 1. CREATE (Protected: Free users can also create, limit logic should be inside)
  create: protectedProcedure.mutation(async ({ ctx }) => {
    return prisma.workflow.create({
      data: {
        name: generateSlug(3),
        userId: ctx.auth.user.id,
        status: "DRAFT", // Default status
        definition: "{}", // Empty definition
      },
    });
  }),

  // 2. REMOVE (Protected)
  remove: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return prisma.workflow.delete({
        where: {
          id: input.id,
          userId: ctx.auth.user.id,
        },
      });
    }),

  // 3. UPDATE SETTINGS (Protected)
  update: protectedProcedure
    .input(
      z.object({
        id: z.string(),
        name: z.string().optional(),
        description: z.string().optional(),
        definition: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...values } = input;
      const userId = ctx.auth.user.id;

      const workflow = await prisma.workflow.findUnique({
        where: { id, userId },
      });

      if (!workflow) {
        throw new TRPCError({ code: "NOT_FOUND" });
      }

      return prisma.workflow.update({
        where: { id, userId },
        data: {
          ...values,
        },
      });
    }),

  // 4. RENAME (Protected)
  updateName: protectedProcedure
    .input(z.object({ id: z.string(), name: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      return prisma.workflow.update({
        where: { id: input.id, userId: ctx.auth.user.id },
        data: { name: input.name },
      });
    }),

  // 🌟 5. DUPLICATE WORKFLOW (PREMIUM ONLY Example)
  // Ye feature sirf premium users use kar sakenge
  duplicate: premiumProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      const userId = ctx.auth.user.id;

      // Original workflow find karo
      const original = await prisma.workflow.findUnique({
        where: { id: input.id, userId },
      });

      if (!original) {
        throw new TRPCError({ code: "NOT_FOUND" });
      }

      // Copy of original workflow create karo
      return prisma.workflow.create({
        data: {
          name: `${original.name} (Copy)`,
          description: original.description,
          definition: original.definition,
          userId,
        },
      });
    }),

  // 6. GET ALL (Protected)
  getMany: protectedProcedure
    .input(
      z.object({
        page: z.number().default(PAGINATION.DEFAULT_PAGE),
        pageSize: z
          .number()
          .min(PAGINATION.MIN_PAGE_SIZE)
          .max(PAGINATION.MAX_PAGE_SIZE)
          .default(PAGINATION.DEFAULT_PAGE_SIZE),
        search: z.string().default(""),
      })
    )
    .query(async ({ ctx, input }) => {
      const { page, pageSize, search } = input;
      const userId = ctx.auth.user.id;

      const whereClause = {
        userId,
        name: {
          contains: search,
          mode: "insensitive" as const,
        },
      };

      const [items, totalCount] = await Promise.all([
        prisma.workflow.findMany({
          skip: (page - 1) * pageSize,
          take: pageSize,
          where: whereClause,
          orderBy: { createdAt: "desc" },
        }),
        prisma.workflow.count({
          where: whereClause,
        }),
      ]);

      const totalPages = Math.ceil(totalCount / pageSize);
      const hasNextPage = page < totalPages;
      const hasPreviousPage = page > 1;

      return {
        items,
        page,
        pageSize,
        totalCount,
        totalPages,
        hasNextPage,
        hasPreviousPage,
      };
    }),

  // 7. GET BY ID (Protected)
  getById: protectedProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ ctx, input }) => {
      const workflow = await prisma.workflow.findUnique({
        where: {
          id: input.id,
          userId: ctx.auth.user.id,
        },
      });

      if (!workflow) {
        throw new TRPCError({ code: "NOT_FOUND" });
      }

      return workflow;
    }),
});
